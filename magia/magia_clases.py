import random
import discord

TAZA_DEFENSA = 0.3


class GameState:

  def __init__(self, wisis, nombre, hechizo):
    self.jugador = Jugador(wisis, nombre, self, hechizo)
    self.enemigo = Enemigo(wisis, self)
    self.turno = 0
    self.decision_jugador = None
    self.decision_enemigo = None
    self.map_cooldown = self.enemigo.map_cooldown
    self.cooldown_hechizo = {}
    self.wealth_diccionario = {}
    self.touch_diccionario = {}
    self.thugfreeze_diccionario = {}
    self.parryados = {}
    self.defensa_diccionario = {}
    self.parry_cooldown = {}
    self.battle_logs = "╭── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╮ \n\n"

  async def sumar_turno(self):
    self.turno += 1

  async def wealth_timer(self):
    wealth_copy = self.wealth_diccionario.copy()
    for objetivo, turno_final in wealth_copy.items():
      if turno_final < self.turno:
        objetivo.isDamageBuff = False
        del self.wealth_diccionario[objetivo]

  async def defensa_timer(self):
    defensa_copy = self.defensa_diccionario.copy()
    for objetivo, turno_final in defensa_copy.items():
      if turno_final < self.turno:
        objetivo.isReducingDamage = False
        del self.defensa_diccionario[objetivo]

  async def touchgangsta_timer(self):
    touch_copy = self.touch_diccionario.copy()
    for objetivo, turno_final in touch_copy.items():
      if turno_final < self.turno:
        del self.touch_diccionario[objetivo]
        return
      bef_vida_jugador = self.jugador.hp
      daño = objetivo.hp_total * 0.1
      objetivo.hp -= round(daño)
      self.battle_logs += f"💀 ``Touch of gangsta`` ha inflingido ``{round(daño)}`` de daño\n❤️``{bef_vida_jugador}`` -> ❤️ ``{self.jugador.hp}``\n"

  async def thugfreeze_timer(self):
    thug_copy = self.thugfreeze_diccionario.copy()
    for objetivo, turno_final in thug_copy.items():
      if turno_final < self.turno:
        objetivo.isFreeze = False
        del self.thugfreeze_diccionario[objetivo]
        return

  async def parry_stun_timer(self):
    parry = self.parryados.copy()
    for objetivo, turno_final in parry.items():
      if turno_final < self.turno:
        objetivo.isStun = False
        del self.parryados[objetivo]
        return

  async def cooldown_hechizos_timer(self):
    cooldown_copy = self.cooldown_hechizo.copy()
    for objetivo, cooldown in cooldown_copy.items():
      if cooldown < self.turno:
        del self.cooldown_hechizo[objetivo]

  async def cooldown_parry_timer(self):
    cooldown_copy = self.parry_cooldown.copy()
    for objetivo, cooldown in cooldown_copy.items():
      if cooldown < self.turno:
        del self.parry_cooldown[objetivo]

  async def battle_logs_restart(self):
    self.battle_logs = "╭── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╮ \n\n"

  async def poll_event(self):

    await self.battle_logs_restart()
    jugador_evento = None
    daño = None
    enemigo_evento = None
    jugador = self.jugador
    enemigo = self.enemigo

    bef_vida_enemiga = round(self.enemigo.hp)
    bef_vida_jugador = round(self.jugador.hp)

    if self.decision_jugador == "Atacar":

      daño = await self.evento_atacar(jugador, enemigo)

      await enemigo.recibir_daño(daño)
      af_vida_enemiga = round(self.enemigo.hp)

      if af_vida_enemiga < 0:
        af_vida_enemiga = 0

    elif self.decision_jugador == "Magia":

      if jugador.magia in [self.stellar_drip, self.holy_sheesh]:

        daño = await jugador.magia(jugador, enemigo)

        if daño == 0:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha fallado!\n\n"

        else:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` hará ``{daño}`` de daño!\n\n"

        await enemigo.recibir_daño(daño)
        af_vida_enemiga = enemigo.hp

        if af_vida_enemiga <= 0:
          af_vida_enemiga = 0

        self.cooldown_hechizo[
          jugador] = self.turno + await self.enemigo.map_cooldown(jugador.magia
                                                                  )

      elif jugador.magia in [self.keez_deez_nuts]:

        bef_vida_jugador = round(self.jugador.hp)

        curacion = round(await jugador.magia(jugador, enemigo))
        self.cooldown_hechizo[
          jugador] = self.turno + await self.enemigo.map_cooldown(jugador.magia
                                                                  )
        af_vida_jugador = round(jugador.hp)

        self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha recuperado ``{curacion}`` de vida!\n❤️``{bef_vida_jugador}`` -> ❤️ ``{af_vida_jugador}``\n\n"

      else:
        acertar = self.jugador.Acertar
        if acertar:
          self.battle_logs += f"¡✨ ``{await nombre_magia(jugador.magia)}`` ha **acertado**!\n\n"
        else:
          self.battle_logs += f"¡💫 ``{await nombre_magia(jugador.magia)}`` ha **fallado**!\n\n"

    elif self.decision_jugador == "Defender":
      x = 1
    elif self.decision_jugador == "Parry":
      x = 1

    else:
      if jugador.isFreeze:
        self.battle_logs += f"🥶 Estás ``congelado``\n\n"
      elif jugador.isStun:
        self.battle_logs += f"😵 Estás ``stuneado``\n\n"

    decision = self.decision_enemigo
    bef_vida_jugador = round(self.jugador.hp)
    bef_vida_enemigo = round(self.enemigo.hp)

    if decision == "Atacar":

      daño = await self.evento_atacar(enemigo, jugador)

      await jugador.recibir_daño(daño)
      af_vida_jugador = round(self.jugador.hp)

      if af_vida_jugador < 0:
        af_vida_jugador = 0

    elif decision == "Magia":

      if enemigo.magia in [self.stellar_drip, self.holy_sheesh]:

        daño = await enemigo.magia(enemigo, jugador)

        if daño == 0:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha fallado!\n\n"

        else:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` hará ``{daño}`` de daño!\n\n"

        await jugador.recibir_daño(daño)
        af_vida_jugador = jugador.hp

        if af_vida_jugador < 0:
          af_vida_jugador = 0

        self.cooldown_hechizo[
          enemigo] = self.turno + await self.enemigo.map_cooldown(enemigo.magia
                                                                  )

      elif enemigo.magia in [self.keez_deez_nuts]:

        bef_vida_enemigo = round(self.enemigo.hp)

        curacion = round(await enemigo.magia(enemigo, jugador))
        self.cooldown_hechizo[
          enemigo] = self.turno + await self.enemigo.map_cooldown(enemigo.magia
                                                                  )

        af_vida_enemiga = round(self.enemigo.hp)

        self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha recuperado ``{curacion}`` de vida!\n❤️``{bef_vida_enemigo}`` -> ❤️ ``{af_vida_enemiga}``\n\n"

      else:

        acertar = self.enemigo.Acertar
        if acertar:
          self.battle_logs += f"¡✨ ``{await nombre_magia(enemigo.magia)}`` ha **acertado**!\n\n"
        else:
          self.battle_logs += f"¡💫 ``{await nombre_magia(enemigo.magia)}`` ha **fallado**!\n\n"

    elif decision == "Defender":
      pass

    else:
      if enemigo.isFreeze:
        self.battle_logs += f"🥶 **{enemigo.name}** está ``congelado``\n\n"
      elif enemigo.isStun:
        self.battle_logs += f"😵 **{enemigo.name}** está ``stuneado``\n\n"

    await self.reiniciar_estados()
    await self.sumar_turno()
    await self.wealth_timer()
    await self.touchgangsta_timer()
    await self.thugfreeze_timer()
    await self.cooldown_hechizos_timer()
    await self.defensa_timer()
    await self.cooldown_parry_timer()
    await self.parry_stun_timer()

    self.battle_logs += "╰── ⋅ ⋅ ── ✩**ACCIONES**✩ ── ⋅ ⋅ ──╯"
    return self.battle_logs

  async def reiniciar_estados(self):
    self.jugador.isDefendido = False
    self.jugador.isReflecting = False
    self.enemigo.isDefendido = False
    self.jugador.isEsquivando = False
    self.enemigo.isEsquivando = False
    self.enemigo.isReflecting = False
    self.enemigo.isNegating = False
    self.jugador.isNegating = False
    self.jugador.Acertar = False
    self.jugador.isParry = False
    self.enemigo.isParry = False
    self.enemigo.Acertar = False
    self.decision_jugador = None
    self.decision_enemigo = None

  async def evento_atacar(self, atacante, objetivo):

    daño = random.randint(int(atacante.daño - 10), int(atacante.daño + 10))

    if atacante.isDamageBuff:
      daño *= 1.8

    return round(daño)

  async def stellar_drip(self, atacante,
                         objetivo):  # Ejecutarse en el poll event, hace daño
    vida_faltante_objetivo = objetivo.hp_total - objetivo.hp
    daño = round(vida_faltante_objetivo * 0.3)

    if atacante.isDamageBuff:
      daño *= 1.8

    return daño

  async def wealth_wraith(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, boosteo de daño
    atacante.isDamageBuff = True
    self.wealth_diccionario[atacante] = self.turno + 2
    return True

  async def gucci_invoker(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, estado actualizado
    probabilidad = random.random()
    if probabilidad < 0.7:
      atacante.isReflecting = True
      return True
    return False

  async def touch_of_gangsta(
      self, atacante,
      objetivo):  # Ejecutarse antes del poll event, estado debuff

    self.touch_diccionario[objetivo] = self.turno + 2
    return True

  async def keez_deez_nuts(self, atacante,
                           objetivo):  # Ejecutarse en el poll event, curacion

    hp_curar = (atacante.hp_total - atacante.hp) * 0.3

    atacante.hp += hp_curar
    return hp_curar

  async def holy_sheesh(self, atacante,
                        objetivo):  # Ejecutarse en el poll event, hace daño
    daño = 0
    if random.random() < 0.5:
      daño = round(objetivo.hp * 0.5)

    return daño

  async def thug_freeze(self, atacante,
                        objetivo):  # Ejecutarse antes del poll event, stun
    if random.random() < 0.5:
      if objetivo.isParry:
        self.parryados[enemigo] = self.turno + 1
        enemigo.isStun = True
        self.battle_logs += f"💫**PARRY!**💫 {enemigo.name} ha sido stuneado 😵‍\n\n"
        self.parry_cooldown[self] = self.turno + 3
        return
      objetivo.isFreeze = True
      self.thugfreeze_diccionario[objetivo] = self.turno + 3
      return True
    return False

  async def is_gameover(self):

    hp_jugador = self.jugador.hp
    hp_enemigo = self.enemigo.hp

    if hp_jugador < 0 and hp_enemigo > 0:
      return "GameOverJugador"

    elif hp_jugador < 0 and hp_enemigo < 0:

      if hp_jugador > hp_enemigo:
        return "GameOverEnemigo"
      else:
        return "GameOverJugador"

    elif hp_enemigo < 0 and hp_jugador > 0:
      return "GameOverEnemigo"

    return None


class Enemigo:

  def __init__(self, wisis, game_state):
    self.wisis = wisis
    self.name = None
    self.daño = None
    self.hp = None
    self.hp_total = None
    self.imagen = None
    self.magia = None
    self.isDefendido = False
    self.isFreeze = False
    self.isStun = False
    self.colour = None
    self.isReflecting = False
    self.Acertar = False
    self.isDamageBuff = False
    self.isParry = False
    self.isNegating = False
    self.objeto = None
    self.winQuote = None
    self.isReducingDamage = False
    self.lostQuote = None
    self.name_mago = None
    self.quotes = None
    self.decidir = None
    self.game_state = game_state

  async def inicializar(self):
    self.name = await self.random_mago(self.wisis)
    self.daño = self.wisis * await self.mago_daño(self.name)
    self.hp = self.wisis * await self.mago_vida(self.name)
    self.objeto = await self.definir_objeto(self.name)
    self.hp_total = self.wisis * await self.mago_vida(self.name)
    self.lostQuote = await self.lost_quote(self.name)
    self.winQuote = await self.win_quote(self.name)
    self.quotes = await self.quotes_func(self.name)
    self.decidir = await self.set_decision(self.name)
    self.imagen = await self.imagen_mago(self.name)
    self.magia = await self.mago_poder(self.name)
    self.colour = await self.color_mago(self.name)

  """ FUNCIONES DE CONSTRUCCIÓN"""

  async def lost_quote(self, name):
    diccionario_lostquote = {
      "Blue Mage":
      "I... don't had... enough drip...",
      "Green Wizard":
      "Thou defeat me... This shalt be destiny",
      "Yellow Sorcerer":
      "It is what it is",
      "Magus Orange":
      "I'll be tellin' da shadow government your achievements",
      "Purple Shadow":
      "Your momma is fat",
      "Red Flame":
      "I guess... This is the end...",
      "Pink Shot":
      "My bullets wasn't good enough? Next time i'll shoot you with some nasty spells"
    }

    return diccionario_lostquote[name]

  async def win_quote(self, name):
    diccionario_winquote = {
      "Blue Mage": "Do thou like those nasty moves",
      "Green Wizard": "This rape was sponsored by the shadow government",
      "Yellow Sorcerer": "My gay detector it's beeping",
      "Magus Orange":
      "Easy as fuck, come back when you can stand those spells",
      "Purple Shadow":
      "Don't worry, thou can try again, i enjoy beating your ass'",
      "Red Flame": "Hueleme el dedo",
      "Pink Shot": "One shot, one kill"
    }

    return diccionario_winquote[name]

  async def quotes_func(self, name):
    diccionario_quotes = {
      "Blue Mage": [
        "Liches be actin' so tough, till you use holy magic",
        "Die already, thou are losing precious magic time",
        "Thou should cast a rope around your neck, NOW!"
      ],
      "Green Wizard": [
        "Thou look like a virgin, i'll cast some bitches for thou",
        "Look at those shiny jewelry, they bright more than your future",
        "Shadow voices are whispering something..."
      ],
      "Yellow Sorcerer": [
        "My magic ball already saw your power, this fight will be effortless",
        "Apoco si muy verga", "Why are thou hurting yourself haha"
      ],
      "Magus Orange": [
        "Don't waste my precious time with those nooby spells",
        "What about casting some hoes", "Your momma goes harder than this"
      ],
      "Purple Shadow": [
        "Let's finish this quickly, i have to bang some witches",
        "Thou shalt summon the spirit lub, cuz this will hurt",
        "Look at this orb, this is where your soul will live forever"
      ],
      "Red Flame": [
        "Little nooby wizard doesn't know he is already lost",
        "I wish i had some draconian zaza...",
        "I can smell your fear, thou are worthless"
      ],
      "Pink Shot": [
        "Prepare to die",
        "I didn't believe in magic till i see your momma affording three niggas at the same time",
        "I trust nothing but the strength of my spells and the edge of my gun"
      ]
    }

    return diccionario_quotes[name]

  async def randomquote(self):
    return self.quotes[random.randint(0, 2)]

  async def random_mago(self, wisis):
    magos = [
      "Blue Mage", "Green Wizard", "Yellow Sorcerer", "Magus Orange",
      "Purple Shadow", "Red Flame", "Pink Shot"
    ]
    probabilidades = [0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2]
    return random.choices(magos, weights=probabilidades)[0]

  async def color_mago(self, name):

    diccionario_color = {
      "Blue Mage": discord.Colour.blue(),
      "Green Wizard": discord.Colour.dark_green(),
      "Yellow Sorcerer": discord.Colour.gold(),
      "Magus Orange": discord.Colour.orange(),
      "Purple Shadow": discord.Colour.dark_purple(),
      "Red Flame": discord.Colour.brand_red(),
      "Pink Shot": discord.Colour.fuchsia()
    }
    return diccionario_color[name]

  async def mago_daño(self, name):
    diccionario_daño = {
      "Blue Mage": 0.13,
      "Green Wizard": 0.17,
      "Yellow Sorcerer": 0.24,
      "Magus Orange": 0.28,
      "Purple Shadow": 0.30,
      "Red Flame": 0.32,
      "Pink Shot": 0.35
    }
    return diccionario_daño[name]

  async def definir_objeto(self, name):

    diccionario_objeto = {
      "Blue Mage": "Zapatos Drip",
      "Green Wizard": "Luna Oscura",
      "Yellow Sorcerer": "Sphaera Ocularis",
      "Magus Orange": "Collar de la Muerte",
      "Purple Shadow": "Joyería Mágica",
      "Red Flame": "Anillo de Ruby",
      "Pink Shot": "Chumbo"
    }

    return diccionario_objeto[name]

  async def mago_vida(self, name):
    diccionario_vida = {
      "Blue Mage": 1.75,
      "Green Wizard": 1.6,
      "Yellow Sorcerer": 1.5,
      "Magus Orange": 1.5,
      "Purple Shadow": 1.4,
      "Red Flame": 1.3,
      "Pink Shot": 1.25
    }
    return diccionario_vida[name]

  async def imagen_mago(self, name):
    diccionario_imagen = {
      "Blue Mage":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116476419598450848/background-remove.png",
      "Green Wizard":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116476666055753738/background-remove.png",
      "Yellow Sorcerer":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116522060349444146/20230607_0342533.png",
      "Magus Orange":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116125599497453629/20230607_034151.jpg",
      "Purple Shadow":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116477569961832508/background-remove.png",
      "Red Flame":
      "https://cdn.discordapp.com/attachments/1029613068788957206/1116523129209102387/imagen.png",
      "Pink Shot":
      "https://cdn.discordapp.com/attachments/1029620174015434772/1116478265033498694/background-remove.png"
    }
    return diccionario_imagen[name]

  async def mago_poder(self, name):

    m = self.game_state
    diccionario_vida = {
      "Blue Mage": m.stellar_drip,
      "Green Wizard": m.wealth_wraith,
      "Yellow Sorcerer": m.gucci_invoker,
      "Magus Orange": m.keez_deez_nuts,
      "Purple Shadow": m.thug_freeze,
      "Red Flame": m.touch_of_gangsta,
      "Pink Shot": m.holy_sheesh
    }
    return diccionario_vida[name]

  async def set_decision(self, name):

    diccionario_decisiones = {
      "Blue Mage": self.decidir_blue,
      "Green Wizard": self.decidir_green,
      "Yellow Sorcerer": self.decidir_yellow,
      "Magus Orange": self.decidir_orange,
      "Purple Shadow": self.decidir_purple,
      "Red Flame": self.decidir_red,
      "Pink Shot": self.decidir_pink
    }

    decidir = diccionario_decisiones[self.name]
    return decidir

  """ FUNCIONES DE FLUJO """

  async def map_cooldown(self, magia):

    m = self.game_state

    dict_cooldown = {
      m.stellar_drip: 3,
      m.wealth_wraith: 4,
      m.gucci_invoker: 3,
      m.touch_of_gangsta: 4,
      m.keez_deez_nuts: 4,
      m.holy_sheesh: 3,
      m.thug_freeze: 4
    }

    return dict_cooldown[magia]

  async def recibir_daño(self, daño):

    if self.isReducingDamage:
      daño *= 0.85
    daño = round(daño)

    jugador = self.game_state.jugador
    gs = self.game_state
    bef_vida_enemigo = round(self.hp)
    bef_vida_jugador = round(jugador.hp)

    if self.isParry:
      daño = 0
      gs.parryados[jugador] = gs.turno + 1
      jugador.isStun = True
      gs.battle_logs += f"💫**PARRY!**💫 ``{jugador.name}`` ha sido stuneado 😵‍\n\n"

    elif self.isDefendido:
      daño *= TAZA_DEFENSA
      daño = round(daño)
      self.hp -= daño
      gs.battle_logs += f"🛡️ El daño ha sido **reducido** a ``{daño}``\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(self.hp)}``\n\n"

    elif self.isReflecting:
      jugador.hp -= daño
      gs.battle_logs += f"🪞 El daño ha sido **reflejado** ``{daño}``\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{jugador.hp}``\n\n"

    else:
      self.hp -= daño
      gs.battle_logs += f"🗡️ ``{self.name}`` ha recibido ``{daño}`` de daño\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(self.hp)}``\n\n"

  async def defenderse(self):
    self.isDefendido = True
    self.isReducingDamage = True
    self.game_state.defensa_diccionario[self] = self.game_state.turno + 2

  async def parry(self):
    self.isParry = True
    self.game_state.parry_cooldown[self] = self.game_state.turno + 2

  """ FUNCIONES DE INTELIGENCIA ARTIFICIAL"""

  async def decidir_red(self):
    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.7, 0.5]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.5
      probabilidades[1] = 0.4
      probabilidades.append(0.6)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 0.8
      probabilidades[0] = 0.1
      probabilidades[1] = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      m = self.game_state

      acertar = await self.magia(m.enemigo, m.jugador)

      m.cooldown_hechizo[m.enemigo] = m.turno + await self.map_cooldown(
        self.magia)
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]

    return decision

  async def decidir_blue(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.8, 0.2]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.7
      probabilidades[1] = 0.6
      probabilidades.append(0.5)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0 - hp_jugador / hp_max_jugador
      probabilidades.append(probabilidad_magia)

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] += 0.2
      probabilidades[0] -= 0.1

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Parry":
      await self.parry()

    gs.decision_enemigo = decision[0]
    return decision

  async def decidir_orange(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.55, 0.35]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.6
      probabilidades[1] = 0.3
      probabilidades.append(0.6)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      if gs.decision_jugador == "Atacar" or (
          gs.decision_jugador == "Magia"
          and gs.jugador.magia in [gs.holy_sheesh, gs.stellar_drip]):
        probabilidad_magia = 1.0
        probabilidades[0] = 0.0
        probabilidades[1] = 0.0

      elif self.hp < (self.hp_total / 3):
        probabilidad_magia = 1.0
      else:
        probabilidad_magia = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      m = self.game_state

      acertar = await self.magia(m.enemigo, m.jugador)

      m.cooldown_hechizo[m.enemigo] = m.turno + await self.map_cooldown(
        self.magia)
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_green(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.5, 0.3]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.6
      probabilidades[1] = 0.3
      probabilidades.append(0.6)

    if not (self.game_state.enemigo in self.game_state.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0
      probabilidades[0] = 0.0
      probabilidades[1] = 0.0
      probabilidades.append(probabilidad_magia)

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] -= 0.1
      probabilidades[0] += 0.3

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    decision = random.choices(decisiones, weights=probabilidades)

    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await self.map_cooldown(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_yellow(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.5, 0.3]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.55
      probabilidades[1] = 0.3
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      if gs.decision_jugador == "Atacar" or (
          gs.decision_jugador == "Magia"
          and gs.jugador.magia in [gs.holy_sheesh, gs.stellar_drip]):
        probabilidad_magia = 0.8
        probabilidades[0] = 0.1
        probabilidades[1] = 0.1
      else:
        probabilidad_magia = 0.1
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if hp_jugador < hp_max_jugador * 0.5:
      probabilidades[1] -= 0.1
      probabilidades[0] += 0.3

    decision = random.choices(decisiones, weights=probabilidades)

    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await self.map_cooldown(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_pink(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.35, 0.65]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades[0] = 0.45
      probabilidades[1] = 0.3
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 1.0
      probabilidades[0] = 0.0
      probabilidades[1] = 0.0
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if gs.enemigo.hp < hp_jugador:
      probabilidades[0] += 0.2
      probabilidades[1] -= 0.2

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Parry":
      await self.parry()

    self.game_state.decision_enemigo = decision[0]
    return decision

  async def decidir_purple(self):

    decisiones = ["Atacar", "Defender"]
    probabilidades = [0.35, 0.65]
    hp_jugador = self.game_state.jugador.hp
    hp_max_jugador = self.game_state.jugador.hp_total
    gs = self.game_state

    if not (gs.enemigo in gs.parry_cooldown):
      decisiones.append("Parry")
      probabilidades.append(0.65)

    if not (gs.enemigo in gs.cooldown_hechizo):
      decisiones.append("Magia")
      probabilidad_magia = 0.8
      probabilidades[0] = 0.2
      probabilidades[1] = 0.2
      probabilidades.append(probabilidad_magia)

    if gs.jugador in gs.parryados:
      probabilidades[0] = 1.0

    if gs.jugador.isFreeze:
      probabilidades[0] = 1.0
      probabilidades[1] = 0.0

    decision = random.choices(decisiones, weights=probabilidades)
    if decision[0] == "Defender":
      await self.defenderse()

    elif decision[0] == "Magia":

      acertar = await self.magia(gs.enemigo, gs.jugador)

      gs.cooldown_hechizo[self] = gs.turno + await self.map_cooldown(self.magia
                                                                     )
      if acertar:
        self.Acertar = True

    elif decision[0] == "Parry":
      await self.parry()
    gs.decision_enemigo = decision[0]
    return decision


class Jugador:

  def __init__(self, wisis, nombre, game_state, hechizo):
    self.wisis = wisis
    self.name = nombre
    self.hechizo = hechizo
    self.magia = None
    self.daño = wisis * 0.2
    self.hp = wisis
    self.hp_total = wisis
    self.isDefendido = False
    self.isParry = False
    self.isReducingDamage = False
    self.isStun = False
    self.isFreeze = False
    self.isDamageBuff = False
    self.isNegating = False
    self.Acertar = False
    self.isReflecting = False
    self.game_state = game_state

  async def atacar(self):
    self.game_state.decision_jugador = "Atacar"

  async def usar_magia(self):

    self.game_state.decision_jugador = "Magia"
    m = self.game_state

    if self.magia in [
        m.wealth_wraith, m.gucci_invoker, m.thug_freeze, m.touch_of_gangsta
    ]:

      acertar = await self.magia(m.jugador, m.enemigo)

      m.cooldown_hechizo[
        m.
        jugador] = self.game_state.turno + await self.game_state.map_cooldown(
          self.magia)
      if acertar:
        self.Acertar = True

  async def recibir_daño(self, daño):

    if self.isReducingDamage:
      daño *= 0.85
    daño = round(daño)
    enemigo = self.game_state.enemigo
    gs = self.game_state
    bef_vida_jugador = round(self.hp)
    bef_vida_enemigo = round(enemigo.hp)

    if self.isParry:
      daño = 0
      gs.parryados[enemigo] = gs.turno + 1
      enemigo.isStun = True
      gs.battle_logs += f" 💫**PARRY!**💫 ``{enemigo.name}`` ha sido stuneado 😵‍\n\n"
      gs.parry_cooldown[self] = gs.turno + 3
      return

    elif self.isDefendido:
      daño *= TAZA_DEFENSA
      daño = round(daño)
      self.hp -= daño
      gs.battle_logs += f"🛡️ El daño ha sido **reducido** a ``{daño}``\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{round(self.hp)}``\n\n"

    elif self.isReflecting:
      enemigo.hp -= daño
      gs.battle_logs += f"🪞 El daño ha sido **reflejado** ``{daño}``\n❤️ ``{bef_vida_enemigo}`` -> ❤️ ``{round(enemigo.hp)}``\n\n"

    else:
      self.hp -= daño
      gs.battle_logs += f"🗡️ Has recibido ``{daño}`` de daño\n❤️ ``{bef_vida_jugador}`` -> ❤️ ``{round(self.hp)}``\n\n"

  async def parry(self):
    self.isParry = True
    self.game_state.parry_cooldown[self] = self.game_state.turno + 2
    self.game_state.decision_jugador = "Parry"

  async def defenderse(self):
    self.game_state.decision_jugador = "Defender"
    self.isDefendido = True
    self.isReducingDamage = True
    self.game_state.defensa_diccionario[self] = self.game_state.turno + 2

  async def inicializar(self):
    m = self.game_state
    diccionario_hechizos = {
      "Stellar Drip": m.stellar_drip,
      "Wealth Wraith": m.wealth_wraith,
      "Gucci Invoker": m.gucci_invoker,
      "Keez Deez Nuts": m.keez_deez_nuts,
      "Thug Freeze": m.thug_freeze,
      "Touch of Gangsta": m.touch_of_gangsta,
      "Holy Sheesh": m.holy_sheesh
    }

    self.magia = diccionario_hechizos[self.hechizo]


async def nombre_magia(funcion):

  nombre = funcion.__name__

  if nombre == "wealth_wraith":
    return "Wealth Wraith"

  elif nombre == "gucci_invoker":
    return "Gucci Invoker"

  elif nombre == "touch_of_gangsta":
    return "Touch of Gangsta"

  elif nombre == "keez_deez_nuts":
    return "Keez Deez Nuts"

  elif nombre == "holy_sheesh":
    return "Holy Sheesh"

  elif nombre == "thug_freeze":
    return "Thug Freeze"

  elif nombre == "stellar_drip":
    return "Stellar Drip"
