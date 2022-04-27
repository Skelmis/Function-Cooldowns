Example Usage
=============

These can be used on any function or method marked with ``async``,
Nextcord is just used for the examples here.

Example bot usage
-----------------

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


Get Remaining Calls
-------------------

.. code-block:: python
    :linenos:

    from cooldowns import get_remaining_calls, cooldown, SlashBucket

    @bot.slash_command()
    @cooldown(2, 10, SlashBucket.command)
    async def test(inter):
        ...
        calls_left = get_remaining_calls(test, inter)
        await inter.send(f"You can call this {calls_left} times before getting rate-limited")


Reset a specific cooldown
-------------------------

Only resets cooldowns for the given id.

.. code-block:: python
    :linenos:

    from cooldowns import cooldown, CooldownBucket, reset_cooldown

    @cooldown(1, 30, CooldownBucket.all, cooldown_id="my_cooldown")
    async def test(*args, **kwargs):
        ...

    # Reset
    reset_cooldown("my_cooldown")


Reset all cooldowns on a callable
---------------------------------

Resets all cooldowns on the provided callable.

.. code-block:: python
    :linenos:

    from cooldowns import cooldown, CooldownBucket, reset_cooldowns

    @cooldown(1, 30, CooldownBucket.all)
    @cooldown(1, 15, CooldownBucket.args)
    async def test(*args, **kwargs):
        ...

    # Reset
    reset_cooldowns(test)

Reset a specific bucket on a cooldown
-------------------------------------

Resets only the given buckets on a cooldown.

.. code-block:: python
    :linenos:

    from cooldowns import cooldown, CooldownBucket, reset_bucket

    @cooldown(1, 30, CooldownBucket.all)
    async def test(*args, **kwargs):
        ...

    ...

    # Reset the bucket with `1` as an argument
    reset_bucket(test, 1)

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


Shared cooldowns
----------------

This allows you to use the same cooldown on multiple callables.

.. code-block:: python
    :linenos:


    from cooldowns import define_shared_cooldown, shared_cooldown, CooldownBucket

    define_shared_cooldown(1, 5, CooldownBucket.all, cooldown_id="my_id")

    @shared_cooldown("my_id")
    async def test_1(*args, **kwargs):
        return 1

    @shared_cooldown("my_id")
    async def test_2(*args, **kwargs):
        return 2

    # These now both share the same cooldown


Manually using cooldowns
------------------------

How to use the Cooldown object without a decorator.

.. code-block:: python
    :linenos:


    from cooldowns import Cooldown, CooldownBucket

    cooldown = Cooldown(1, 5, CooldownBucket.args)

    async with cooldown:
        # This will apply the cooldown
        ...
        # Do things
