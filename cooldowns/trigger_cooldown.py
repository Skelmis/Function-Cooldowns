
import asyncio
import datetime
import inspect
import functools
from typing import Callable, Optional, Union
from .cooldown import Cooldown

from .utils import (
    MaybeCoro,
    maybe_coro,
    default_check,
)

from . import utils
from .protocols import CooldownBucketProtocol

class TriggerCooldown:
    def __init__(
            self,
            limit: int,
            time_period: Union[float, datetime.timedelta],
            bucket: Optional[CooldownBucketProtocol] = None,
            *,
            cooldown_id: Optional[Union[int, str]] = None,
            trigger_cooldown_id: Optional[Union[int, str]] = None,
            check: Optional[MaybeCoro] = default_check,
    ):
        """
        Creates a trigger cooldown.

        This is useful if you want to be able to trigger a specific time_period cooldown
        inside the command itself.

        TriggerCooldown creates two cooldonws in one instance:

        - Normal cooldown. The same cooldown as @cooldowns.cooldown()
        - Trigger cooldown. A secondary cooldown that can only be activate
        with `.trigger()`

        Parameters
        ----------
        limit : `int`
            How many call's can be made in the time
            period specified by ``time_period``.

        time_period : `Union[float, datetime.timedelta]`
            The time period related to ``limit``. This is seconds.

        bucket : `Optional[CooldownBucketProtocol], optional`
            The :class:`Bucket` implementation to use
            as a bucket to separate cooldown buckets.

        check : `Optional[MaybeCoro], optional`
            A Callable which dictates whether
            to apply the cooldown on current invoke.

            If this Callable returns a truthy value,
            then the cooldown will be used for the current call.

            I.e. If you wished to bypass cooldowns, you
            would return False if you invoked the Callable.
        
        cooldown_id: Optional[Union[int, str]]
            Useful for resetting individual stacked cooldowns.
            This should be unique globally,
            behaviour is not guaranteed if not unique.

            .. note::

                This check will be given the same arguments as
                the item you are applying the cooldown to.
        
        Usage
        -----
            - First create an instance of TriggerCooldown() with
            the desired parameters.

            ```
            trigger_cooldown = cooldowns.TriggerCooldown(1, 5, cooldowns.SlashBucket.author)
            ```
            
            - Then add the instance as a decorator to your command!

            ```
            @nextcord.slash_command()
            @trigger_cooldown
            async def command():
            ```

                The instance has to be defined in the same scope as the decorator!
                Now, `command()` has applied a normal cooldown of `1 limit` and
                `5 time_period`, as we defined it.

            - Finally, inside your command, you can `trigger` the trigger cooldown:

            ```
            async def command():
                # Do things
                trigger_cooldown.trigger(30)
                # You can still do things after this.
                # Even you can `interaction.send()`.
            ```

                From the moment when the cooldown was triggered by `.trigger(30)`, every
                single call to this command within 30 seconds will raise CallableOnCooldown!
        
        Raises
        ------
        `RuntimeError`
            Expected the decorated function to be a coroutine.
        `CallableOnCooldown`
            This call resulted in a cooldown being put into effect.
        """

        self.triggered = False

        self.limit = limit
        self.time_period = time_period
        self.bucket = bucket
        self.cooldown_id = cooldown_id
        self.trigger_cooldown_id = trigger_cooldown_id
        self.check = check

        # Normal Cooldown
        self.cooldown = Cooldown(
                limit= self.limit,
                time_period= self.time_period,
                bucket= self.bucket,
                cooldown_id= self.cooldown_id,
                check= self.check
            )

        # Trigger Cooldown
        self.trigger_cooldown = Cooldown(
                limit= 1,
                time_period= self.time_period,
                bucket= self.bucket,
                cooldown_id= self.trigger_cooldown_id,
                check= self.check
            )

        if cooldown_id:
            utils.shared_cooldown_refs[cooldown_id] = self.cooldown

        else:
            current_cooldowns = utils.shared_cooldown_refs.keys()
            for i in range(10_000):
                generated_id = f"normal_cooldown_{i:02}"
                if generated_id not in current_cooldowns:
                    utils.shared_cooldown_refs[generated_id] = self.cooldown
                    self.cooldown_id = generated_id

        if trigger_cooldown_id:
            utils.shared_cooldown_refs[trigger_cooldown_id] = self.trigger_cooldown

        else:
            current_cooldowns = utils.shared_cooldown_refs.keys()
            for i in range(10_000):
                generated_id = f"trigger_cooldown_{i:02}"
                if generated_id not in current_cooldowns:
                    utils.shared_cooldown_refs[generated_id] = self.trigger_cooldown
                    self.trigger_cooldown_id = generated_id

    async def trigger(self, time_period: Union[float, datetime.timedelta]) -> None:
        """|coro|

        Trigger the Trigger Cooldown instantly. Has to be awaited.

        Parameters
        ----------
        time_period : `Union[float, datetime.timedelta]`
            The time period that cooldwon will remain triggered.
        """
        self.triggered = True
        self.trigger_cooldown.time_period = (
            time_period
            if isinstance(time_period, (float, int))
            else time_period.total_seconds()
        )

        # Triggers the Cooldown leaving bucket.current = 0
        frame = inspect.currentframe().f_back
        _, _, _, values = inspect.getargvalues(frame)
        args = tuple(values.values())

        async with self.trigger_cooldown(*args):
            return None


    def __call__(self, func: Callable) -> Callable:
        """
        
        Called as a decorator.

        Parameters
        ----------
        func : `Callable`
            The function being decorated.

        Returns
        -------
        `Callable`
            Decorator

        Raises
        ------
        `RuntimeError`
            When given function is not coroutine.
        """

        _cooldown: Cooldown = utils.shared_cooldown_refs[self.cooldown_id]
        _trigger_cooldown: Cooldown = utils.shared_cooldown_refs[self.trigger_cooldown_id]

        if not asyncio.iscoroutinefunction(func):
            raise RuntimeError(
                f"Expected `func` to be a coroutine, "
                f"found {func} of type {func.__class__.__name__!r} instead"  # noqa
            )
        # Links the cooldowns to the given function.
        _cooldown._func = func
        _trigger_cooldown._func = func

        attached_cooldowns = getattr(func, "_cooldowns", [])

        if _cooldown not in attached_cooldowns:
            attached_cooldowns.append(_cooldown)

        if _trigger_cooldown not in attached_cooldowns:
            attached_cooldowns.append(_trigger_cooldown)

        setattr(func, "_cooldowns", attached_cooldowns)

        @functools.wraps(func)
        async def inner(*args, **kwargs):
            use_cooldown = await maybe_coro(self.check, *args, **kwargs)
            if not use_cooldown:
                return await maybe_coro(func, *args, **kwargs)

            self_arg = None
            if "self" in kwargs:
                self_arg = kwargs.pop("self")

            # If the cooldown is triggered...
            # if self.triggered:
            # If still on triggered cooldown...
            if _trigger_cooldown.remaining_calls(*args, **kwargs) < 1:
                # Runs the Trigger Cooldown.
                async with _trigger_cooldown(*args, **kwargs):
                    if self_arg:
                        kwargs["self"] = self_arg
                        result = await func(*args, **kwargs)
                    else:
                        result = await func(*args, **kwargs)
                return result
                # If not, untrigger the cooldown.
                # else:
                #     self.triggered = False
            # If the cooldown is not triggered.
            # Runs the normal Cooldown.
            async with _cooldown(*args, **kwargs):
                if self_arg:
                    kwargs["self"] = self_arg
                    result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                return result
        # Return the decorator.
        return inner
