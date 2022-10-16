Function Cooldowns
---

A simplistic take on functional cooldowns. 

`pip install function-cooldowns`


---

### Example usage

A simplistic example, read more on the docs!

```python
import cooldowns

...

@bot.slash_command(
    description="Ping command",
)
@cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
async def ping(interaction: nextcord.Interaction):
    await interaction.response.send_message("Pong!")
```

---

#### Find more examples [here](https://function-cooldowns.readthedocs.io/en/latest/modules/examples.html).

#### For documentation, please see [here](https://function-cooldowns.readthedocs.io/en/latest/).

#### This implements the [leaky bucket](https://en.wikipedia.org/wiki/Leaky_bucket) algorithm

---

### Support

Want realtime help? Join the discord [here](https://discord.gg/BqPNSH2jPg).

---

### Funding

Want a feature added quickly? Want me to help build your software using this?

Sponsor me [here](https://github.com/sponsors/Skelmis)
