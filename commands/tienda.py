import discord
from discord.ext import commands
from main import client
from datetime import datetime, timedelta
from typing import Literal
import asqlite

""" Modulo de tienda
TO-DO:
async def choosecolour(
  interaction: Interaction,
  colour: Literal["Red", "Green", "Blue"]
):
  print(colour)
  # will print either Red, Green or Blue
"""

async def errorEmbed(razon_error):
    embed = discord.Embed(title="¡Oops! Sucedió un error al ejecutar el comando",
                        description=f"**Razon**: {razon_error}",
                        colour=discord.Colour.blue())
    embed.set_image(url="https://img1.picmix.com/output/stamp/normal/6/9/9/1/1921996_759c3.gif")

    return embed

async def get_objetoid(nombre_objeto):
    async with asqlite.connect('wisis.db') as con:
        async with con.cursor() as cur:
            await cur.execute("SELECT objeto_id FROM objetos WHERE nombre = ?",(nombre_objeto,))
            resultado = await cur.fetchone()

            if resultado is None:
                return None
            return resultado[0]



class Tienda(commands.Cog): #Clase de cog para los comandos
    
    def __init__(self, client: commands.Bot):
        self.client = client
    


    @commands.hybrid_command(name="tienda", description="Muestra la tienda")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def tienda(self, ctx):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT nombre, valor, descripcion FROM objetos")
                objetos = await cur.fetchall()

                embed = discord.Embed(title="🛍️ Tienda",
                                    description="*Para comprar usa ``comprar <objeto> <cantidad>``*",
                                    colour=discord.Colour.random())

                for objeto in objetos:
                    nombre = objeto[0]
                    valor = objeto[1]
                    descripcion = objeto[2]
                    embed.add_field(name=f"{nombre}",value=f"<:whezze:1029620490408574987> **{valor}**\n{descripcion}",inline=False)

                await ctx.send(embed=embed)




    @commands.hybrid_command(name="comprar", description="Compra un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def comprar(self, ctx, objeto: str, cantidad: int):

        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                # Verificar si el objeto existe en la base de datos
                await cur.execute("SELECT objeto_id, valor FROM objetos WHERE nombre = ?", (objeto,))
                resultado = await cur.fetchone()

                if resultado == None:
                    await ctx.send(embed=await errorEmbed("No existe este objeto"))
                    return

                if cantidad < 0:
                    await ctx.send(embed=await errorEmbed("Se ha especificado una cantidad negativa"))
                    return

                # Asignar los datos de la query anterior a dos variables
                valor = resultado[1] * cantidad
                objeto_id = resultado[0]

                # Verificar wisis del usuario
                await cur.execute("SELECT wisis FROM usuarios WHERE usuario_id = ?", (ctx.author.id,))
                resultado = await cur.fetchone() 

                if resultado[0] < valor:
                    embed = discord.Embed(title="No tienes wisis suficientes!",
                                        description=f"Tus <:whezze:1029620490408574987>: **{resultado[0]}**\nCoste de **{objeto} x{cantidad}**: <:whezze:1029620490408574987> **{valor}**",
                                        colour=discord.Colour.red())
                    await ctx.send(embed=embed)
                    return

                # Verificar si el objeto ya existe en el inventario
                await cur.execute("SELECT usuario_id FROM inventario WHERE objeto_id = ? AND usuario_id = ?", (objeto_id, int(ctx.author.id)))
                resultado = await cur.fetchone()

                # Si no existe, crea una row en la db, si existe, actualiza el valor de la cantidad
                if resultado == None:
                    await cur.execute("INSERT INTO inventario (usuario_id, objeto_id, cantidad) VALUES (?, ?, ?)",
                                (int(ctx.author.id), objeto_id, cantidad))
                else:
                    await cur.execute("UPDATE inventario SET cantidad = cantidad + ? WHERE usuario_id = ? AND objeto_id = ?", (cantidad, int(ctx.author.id), objeto_id))

                await cur.execute("UPDATE usuarios SET wisis = wisis - ? WHERE usuario_id = ?", (valor, int(ctx.author.id)))
                await cur.execute("SELECT wisis FROM usuarios WHERE usuario_id = ?", (int(ctx.author.id),))
                wisis = await cur.fetchone()

                embed = discord.Embed(title="✅  Compra realizada",
                                    description=f"Haz comprado ``x{cantidad} {objeto}`` por el valor de <:whezze:1029620490408574987> **{valor}**\n<:whezze:1029620490408574987> actuales: {wisis[0]}",
                                    colour= discord.Colour.green())
                await ctx.send(embed=embed)

                await con.commit()

        

    @commands.hybrid_command(name="objeto", description="Muestra información sobre un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def objeto(self, ctx, objeto: str):
        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                await cur.execute("SELECT nombre, valor, descripcion FROM objetos WHERE nombre = ?", (objeto,))
                resultado = await cur.fetchone()

                if resultado == None:
                    await ctx.send(embed=await errorEmbed("No se ha encontrado el objeto en la base de datos"))
                    return

                nombre, valor, descripcion = resultado[0], resultado[1], resultado[2]

                embed = discord.Embed(title=f"{nombre}", description=f"{descripcion}\n\n**Valor:** <:whezze:1029620490408574987>``{valor}``", colour=discord.Colour.random())
                await ctx.send(embed=embed)


    @commands.hybrid_command(name="usar", description="Usa un objeto")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def usar(self, ctx, objeto: str, usuario: discord.Member =None):
        # Obtener la ID del objeto
        objeto_id = await get_objetoid(objeto)

        if objeto_id == None: # Si no hay ID, el objeto no existe
            await ctx.send(embed=await errorEmbed("No se ha encontrado el objeto en la base de datos"))
            return

        if usuario == None:
            usuario = ctx.author

        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:
                #Buscar por la cantidad de ese objeto en el inventario
                await cur.execute("SELECT cantidad FROM inventario WHERE usuario_id = ? AND objeto_id = ?", (int(ctx.author.id), objeto_id))
                cantidad = await cur.fetchone()

                if cantidad == None or cantidad[0] == 0:
                    await ctx.send(f"No tienes ningun **{objeto}** en tu inventario") 
                    return

                if objeto == "BanTicket":

                    if usuario in ctx.guild.premium_subscribers: #Tiene nitro, no puede banearlo
                        embed = discord.Embed(title="No se puede usar el BanTicket", description=f"El usuario: ``{usuario.name}`` es nitro booster", colour=discord.Colour.random())
                        await ctx.send(embed=embed)
                        return

                    await cur.execute("SELECT antilloros FROM usuarios WHERE usuario_id = ?", (int(usuario.id),))
                    cantidad = await cur.fetchone()

                    if cantidad[0] == 0: # No tiene antilloros

                        unban_time = datetime.utcnow() + timedelta(hours=24)

                        # Enviar DM al usuario avisandole de baeneo
                        embed = discord.Embed(title=f"BanTicket 24h", description=f"Reclamado por: **{ctx.author.name}**\nFinaliza en: **{unban_time}**",
                                            colour=discord.Colour.random(), timestamp=datetime.utcnow())
                        channel = await self.client.create_dm(usuario)
                        await channel.send(embed=embed)

                        # Banear al usuario

                        await cur.execute('INSERT OR REPLACE INTO tempbans (user_id, unban_time) VALUES (?, ?)', (int(usuario.id), unban_time.timestamp()))
                        await usuario.ban(reason=f"BanTicket de 24 horas reclamado.\nUsuario que reclamó: {ctx.author.name}\nTiempo de vencimiento: {unban_time}")

                        #Consumir un banticket
                        await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",(ctx.author.id, objeto_id))


                        #Devolver operacion completada con éxito
                        embed = discord.Embed(title=f"¡{objeto} usado con éxito!",
                                            description=f"El objeto ``{objeto}`` ha sido usado en ``{usuario.name}``",
                                            colour=discord.Colour.random())
                        await ctx.send(embed=embed)
                        return

                    else: # Tiene antilloros
                        #Consumir el antilloros
                        await cur.execute("UPDATE usuarios SET antilloros = antilloros - 1 WHERE usuario_id = ?", (int(usuario.id),))

                        #Enviar mensaje que se ha consumido y no se pudo banear
                        await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",(ctx.author.id, objeto_id))
                        embed = discord.Embed(title=f"¡{objeto} ha sido usado!",
                                            description=f"El objeto ``{objeto}`` ha sido usado en ``{usuario.name}``\n¡Un antilloros del usuario se ha gastado!",
                                            colour=discord.Colour.random())

                        await ctx.send(embed=embed)
                        return

    


                elif objeto == "TimeoutTicket":

                    '''TO DO
                    -Escribir al dm del muteado
                    -Consumir un banticket del inventario'''

                    #Verificar si tiene antilloros, si tiene, consumir el antilloros y gastar el objeto, si no tiene, gastar el objeto y continuar
                    async with asqlite.connect('wisis.db') as con:
                        async with con.cursor() as cur:
                            await cur.execute("SELECT antilloros FROM usuarios WHERE usuario_id = ?", (usuario.id,))
                            resultado = await cur.fetchone()

                            if resultado[0] >= 1:
                                await cur.execute("UPDATE usuarios SET antilloros = antilloros - 1 WHERE usuario_id = ?", (int(usuario.id),))

                                #Enviar mensaje que se ha consumido y no se pudo banear
                                await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",(ctx.author.id, objeto_id))
                                embed = discord.Embed(title=f"¡{objeto} ha sido usado!",
                                                    description=f"El objeto ``{objeto}`` ha sido usado en ``{usuario.name}``\n\n¡Un antilloros del usuario se ha gastado!",
                                                    colour=discord.Colour.random())

                                await ctx.send(embed=embed)
                                return

                            else:
                                await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?",(ctx.author.id, objeto_id))




                    # Intentar hacer timeout, si no se puede, remover admin y luego hacer timeout
                    try:
                        await usuario.timeout(discord.utils.utcnow() + timedelta(hours=24), reason="Timeout")

                    except Exception as e:
                        await usuario.remove_roles(usuario.top_role)
                        await usuario.timeout(discord.utils.utcnow() + timedelta(hours=24), reason="Timeout")


                    # Envia mensaje al usuario
                    embed = discord.Embed(title=f"TimeoutTicket 24h", description=f"Reclamado por: **{ctx.author.name}**\nFinaliza en: **{datetime.utcnow() + timedelta(hours=24)}**",
                                            colour=discord.Colour.random(), timestamp=datetime.utcnow())
                    channel = await self.client.create_dm(usuario)
                    await channel.send(embed=embed)


                    # Envía mensaje al canal
                    embed = discord.Embed(title=f"¡{objeto} usado con éxito!",
                                            description=f"El objeto ``{objeto}`` ha sido usado en ``{usuario.name}``",
                                            colour=discord.Colour.random())
                    await ctx.send(embed=embed)


                elif objeto == "Rol":
                    '''TO DO:
                    -Enviar mensajes para inputs del rol
                    -Darle el rol al usuario
                    -Consumir el objeto'''
                    pass

                elif objeto == "Antilloros":

                    #Aplicar antilloros al usuarip
                    await cur.execute("UPDATE usuarios SET antilloros = antilloros + 1 WHERE usuario_id = ?", (usuario.id,))


                    #Consumir antilloros
                    await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?", (usuario.id,objeto_id))
                    embed = discord.Embed(title=f"¡{objeto} ha sido usado con éxito!",
                                        description=f"Se ha aplicado en ``{usuario.display_name}``",
                                        colour=discord.Colour.random())

                    await ctx.send(embed=embed)
                    return

    @commands.hybrid_command(name="usar_rol", description="Usa el objeto 'Rol' ")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def usar_rol(self, ctx, nombre : str, color : str):


        async with asqlite.connect('wisis.db') as con:
            async with con.cursor() as cur:

                objeto_id = await get_objetoid("Rol")
                # Revisar si tiene el objeto en su inventario
                await cur.execute("SELECT cantidad FROM inventario WHERE usuario_id = ? AND objeto_id = ?", (ctx.author.id, objeto_id))
                resultado = await cur.fetchone()

                if resultado is None:
                    await ctx.send("No tienes el objeto **'Rol'** en tu inventario")
                    return

                if resultado[0] == 0:
                    await ctx.send("No tienes el objeto **'Rol'** en tu inventario")
                    return

                try:
                    rol = await ctx.guild.create_role(name=nombre, color=discord.Colour.from_str(color))
                except Exception as e:
                    await ctx.send(embed=errorEmbed("Hubo un error al crear el rol, comprueba si los parametros indicados son correctos"))
                    return


                await cur.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE usuario_id = ? AND objeto_id = ?", (ctx.author.id, objeto_id))
                embed = discord.Embed(title=f"¡'Rol' ha sido usado con éxito!",
                                        description=f"Rol: {rol.mention}\nConsulta con un administrador para ponerle una imagen",
                                        colour=discord.Colour.random())

                await ctx.author.add_roles(rol)

                await ctx.send(embed=embed)



    	




async def setup(client):
    await client.add_cog(Tienda(client))