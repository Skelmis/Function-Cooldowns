Nextcord Slash Cooldown's
=========================

Given the lack of official support,
here is how to use cooldown's (unofficially).

``pip install function-cooldowns``

Check out the Github `here <https://github.com/Skelmis/Function-Cooldowns>`_

Want support? Broke something? Ask me in the nextcord discord, ``Skelmis#9135``

Decorator arguments
-------------------

.. code-block:: python
    :linenos:

    def cooldown(
        limit: int,
        time_period: float,
        bucket: CooldownBucketProtocol,
        check: Optional[MaybeCoro] = lambda *args, **kwargs: True,
    ):



limit: int
    How many call's can be made in the time
    period specified by ``time_period``
time_period: float
    The time period related to ``limit``
bucket: CooldownBucketProtocol
    The :class:`Bucket` implementation to use
    as a bucket to separate cooldown buckets.
check: Optional[MaybeCoro]
    A Callable which dictates whether or not
    to apply the cooldown on current invoke.

    If this Callable returns a truthy value,
    then the cooldown will be used for the current call.

    I.e. If you wished to bypass cooldowns, you
    would return False if you invoked the Callable.


Possible buckets
----------------

Most basic bucket.

.. code-block:: python
    :linenos:

    from cooldowns import CooldownBucket

    CooldownBucket.all
    CooldownBucket.args
    CooldownBucket.kwargs

    """
    A collection of generic CooldownBucket's for usage in cooldown's.

    Attributes
    ==========
    all
        The buckets are defined using all
        arguments passed to the :type:`Callable`
    args
        The buckets are defined using all
        non-keyword arguments passed to the :type:`Callable`
    kwargs
        The buckets are defined using all
        keyword arguments passed to the :type:`Callable`
    """


Slash command bucket.

.. code-block:: python
    :linenos:

    from cooldowns import SlashBucket

    SlashBucket.author
    SlashBucket.guild
    SlashBucket.channel
    SlashBucket.command

    """
    A collection of generic cooldown bucket's for usage
    with nextcord slash commands which take ``Interaction``

    Attributes
    ==========
    author
        Rate-limits the command per person.
    guild
        Rate-limits the command per guild.
    channel
        Rate-limits the command per channel
    command
        Rate-limits the entire command as one.
    """


Example usage
-------------

Rate-limits the command to ``1`` call per person
every ``15`` seconds in your main file.

.. code-block:: python
    :linenos:

    import cooldowns

    ...

    @bot.slash_command(
        description="Ping command",
    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def ping(interaction: nextcord.Interaction):
        await interaction.response.send_message("Pong!")


Example cog usage
-----------------

Rate-limits the command to ``1`` call per
guild every ``30`` seconds.

.. code-block:: python
    :linenos:

    import cooldowns

    ...

    @nextcord.slash_command(
        description="Ping command",
    )
    @cooldowns.cooldown(1, 30, bucket=cooldowns.SlashBucket.guild)
    async def ping(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("Pong!")


Handling cooldown's
-------------------

Here is an example error handler

.. code-block:: python
    :linenos:

    from cooldowns import CallableOnCooldown

    ...

    @bot.event
    async def on_application_command_error(inter: nextcord.Interaction, error):
        error = getattr(error, "original", error)

        if isinstance(error, CallableOnCooldown):
            await inter.send(
                f"You are being rate-limited! Retry in `{error.retry_after}` seconds."
            )

        else:
            raise error


The error ``CallableOnCooldown`` has the following attributes.

func: Callable
    The `Callable` which is currently rate-limited
cooldown: Cooldown
    The :class:`Cooldown` which applies to the current cooldown
retry_after: float
    How many seconds before you can retry the `Callable`
resets_at: datetime.datetime
    The exact datetime this cooldown resets.


Get remaining calls
-------------------

Definition

.. code-block:: python
    :linenos:

    def get_remaining_calls(func: MaybeCoro, *args, **kwargs) -> int:
        """
        Given a :type:`Callable`, return the amount of remaining
        available calls before these arguments will result
        in the callable being rate-limited.

        Parameters
        ----------
        func: MaybeCoro
            The :type:`Callable` you want to check.
        args
            Any arguments you will pass.
        kwargs
            Any key-word arguments you will pass.

        Returns
        -------
        int
            How many more times this :type:`Callable`
            can be called without being rate-limited.

        Raises
        ------
        NoRegisteredCooldowns
            The given :type:`Callable` has no cooldowns.

        Notes
        -----
        This aggregates all attached cooldowns
        and returns the lowest remaining amount.
        """

Example usage

.. code-block:: python
    :linenos:

    from cooldowns import get_remaining_calls, cooldown, SlashBucket

    @bot.slash_command()
    @cooldown(2, 10, SlashBucket.command)
    async def test(inter):
        ...
        calls_left = get_remaining_calls(test, inter)
        await inter.send(f"You can call this {calls_left} times before getting rate-limited")


Cooldown checks
---------------

Here's an example check to only apply a cooldown
if the first argument is equal to ``1``.

.. code-block:: python
    :linenos:

    @cooldown(
        1, 1, bucket=CooldownBucket.args, check=lambda *args, **kwargs: args[0] == 1
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

Here's one use an async check.
Functionally its the same as the previous one.

.. code-block:: python
    :linenos:

    async def mock_db_check(*args, **kwargs):
        # You can do database calls here or anything
        # since this is an async context
        return args[0] == 1

    @cooldown(1, 1, bucket=CooldownBucket.args, check=mock_db_check)
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs


Custom buckets
--------------

All you need is an enum with the ``process`` method.

Heres an example which rate-limits based off of the first argument.

.. code-block:: python
    :linenos:

    class CustomBucket(Enum):
        first_arg = 1

        def process(self, *args, **kwargs):
            if self is CustomBucket.first_arg:
                # This bucket is based ONLY off
                # of the first argument passed
                return args[0]

    # Then to use
    @cooldown(1, 1, bucket=CustomBucket.first_arg)
    async def test_func(*args, **kwargs):
        .....


Stacking cooldown's
-------------------

Stack as many cooldown's as you want, just note
Python starts from the bottom decor and works its way up.

.. code-block:: python
    :linenos:

    # Can call ONCE time_period second using the same args
    # Can call TWICE time_period second using the same kwargs
    @cooldown(1, 1, bucket=CooldownBucket.args)
    @cooldown(2, 1, bucket=CooldownBucket.kwargs)
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs