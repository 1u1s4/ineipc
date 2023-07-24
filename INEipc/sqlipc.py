import pkg_resources
import configparser
from getpass import getpass
import warnings
from typing import List, Tuple

warnings.filterwarnings("ignore")
import os

import numpy as np
import pandas as pd
import datetime

from utilsjo import mes_by_ordinal, r0und
from INEcodex import Codex
from INEfnts import Fuentes

class SqlIPC:
    def __init__(self, anio: int, mes: int, dbBackup: bool=False, dbPack: bool=False) -> None:
        # cargar Codex
        self.__codex = Codex()
        self.__codex.cargar_clave()
        self.anio = anio
        self.mes = mes
       # diccionario tipo de fuentes
        self.nombre_fuentes = {
            0: 'Sin tipo',#SIN TIPO DE FUENTE ASIGNADO
            1: 'Carnicerias',#CARNICERIAS, MARRANERIAS, POLLERIAS, ETC.
            2: 'Supermercados',#SUPERMERCADOS, DESPENSAS Y ALMACENES EN CADENA
            3: 'Hipermercados',#HIPERMERCADOS
            4: 'Depositos',#DEPOSITOS Y ABARROTERIAS
            5: 'Tiendas no Especializadas',#TIENDAS NO ESPECIALIZADAS (INCLUYE MISCELANEAS Y TIENDAS DE
            6: 'Almacenes',#ALMACENES O TIENDAS ESPECIALIZADAS
            7: 'Restaurantes',#RESTAURANTES  O EXPENDIOS DE COMIDAS PREPARADAS EN CADENA
            8: 'Empresas',#EMPRESAS ESPECIALIZADAS EN PRESTACION DE SERVICIOS
            9: 'Expendios de Gas',#EXPENDIOS DE GAS PROPANO
            10: 'Farmacias',#FARMACIAS, DROGUERIAS Y PERFUMERIAS
            11: 'Centros de Salud',#HOSPITALES, CLINICAS, CENTROS Y PUESTOS DE SALUD, LABORATORI
            12: 'Hoteles',#HOTELES, MOTELES, HOSPEDAJES, PENSIONES Y ALOJAMIENTOS
            13: 'Centros Educativos',#COLEGIOS, ACADEMIAS,  INSTITUTOS, UNIVERSIDADES Y OTROS
            14: 'Otros Establecimientos Especializados',#OTROS ESTABLECIMIENTOS ESPECIALIZADOS EN PREPARACION DE SERV
            15: 'Servicio Domestico',#SERVICIO DOMESTICO
            16: 'Otros Establecimientos No Especializados',#OTROS ESTABLECIMIENTOS NO ESPECIALIZADOS EN OTRO CODIGO
            20: 'Cuarto de Alquiler',#VIVIENDA TIPO CUARTO DE ALQUILER
            21: 'Apartamento de Alquiler',#VIVIENDA TIPO APARTAMENTO DE ALQUILER
            22: 'Casa de Alquiler',#VIVIENDA TIPO CASA DE ALQUILER
            23: 'Mercados',#MERCADOS CANTONALES Y MUNICIPALES ( COMPRA DE ALIMENTOS )
        }
        if dbBackup:
            self.df_DivInd = self.__codex.cargar_df('db_b/df_DivInd.parquet')
            self.df_DivPon = self.__codex.cargar_df('db_b/df_DivPon.parquet')
            self.df_GbaInd = self.__codex.cargar_df('db_b/df_GbaInd.parquet')
            self.df_GbaPon = self.__codex.cargar_df('db_b/df_GbaPon.parquet')
            self.df_GbaInfo = self.__codex.cargar_df('db_b/df_GbaInfo.parquet')
            self.df_DivNom = self.__codex.cargar_df('db_b/df_DivNom.parquet')
            self.df_Fnt = self.__codex.cargar_df('db_b/df_Fnt.parquet')
        elif dbPack:
            self.df_DivInd = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_DivInd.parquet'))
            self.df_DivPon = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_DivPon.parquet'))
            self.df_GbaInd = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_GbaInd.parquet'))
            self.df_GbaPon = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_GbaPon.parquet'))
            self.df_GbaInfo = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_GbaInfo.parquet'))
            self.df_DivNom = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_DivNom.parquet'))
            self.df_Fnt = self.__codex.cargar_df(pkg_resources.resource_filename(__name__, 'db_pack/df_Fnt.parquet'))
        else:
            # datos servidor
            DATABASE = "IPC2010_RN"
            if os.path.exists('config.ini'):
                config = configparser.ConfigParser()
                config.read('config.ini')
                db_config = config['database']
                SERVER, USERNAME, PASSWORD = db_config['SERVER'], db_config['USERNAME'], db_config['PASSWORD']
            elif all([os.getenv('SERVER'), os.getenv('USERNAME'), os.getenv('PASSWORD')]):
                SERVER, USERNAME, PASSWORD = os.getenv('SERVER'), os.getenv('USERNAME'), os.getenv('PASSWORD')
            else:
                print('Datos de conexión no encontrados. Ingrese los datos de conexión a la base de datos:')
                os.environ['SERVER'] = input('Servidor: ')
                os.environ['USERNAME'] = input('Usuario: ')
                os.environ['PASSWORD'] = input('Contraseña: ')
                SERVER, USERNAME, PASSWORD = os.getenv('SERVER'), os.getenv('USERNAME'), os.getenv('PASSWORD')
            # conexion
            import pyodbc
            self.__conexion = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server}'
                + f';SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
            )
            # extractor de boletas
            fuentes = Fuentes(self.__conexion)
            self.df_DivNom = pd.read_sql(
                'SELECT DivCod, DivNom FROM IPCM01',
                self.__conexion
            )
            # ponderaciones de las divisiones
            self.df_DivPon = pd.read_sql(
                f'SELECT RegCod, DivCod, DivPon FROM IPCP01',
                self.__conexion
            )
            self.df_DivPon = self.df_DivPon.astype({'RegCod': 'int64', 'DivCod': 'int64'})
            # ponderaciones de los gastos basicos
            self.df_GbaPon = pd.read_sql(
                f'SELECT RegCod, DivCod, GbaCod, GbaPon FROM IPCP05',
                self.__conexion
            )
            columnas = ("RegCod", "DivCod", "GbaCod")
            self.df_GbaPon = self.df_GbaPon.astype(dict.fromkeys(columnas, "int64"))
            # informacion gastos basicos
            self.df_GbaInfo = pd.read_sql(
                'SELECT DivCod, AgrCod, GruCod, SubCod, GbaCod, GbaNom FROM IPCM05',
                self.__conexion
            )
            columnas = ('DivCod', 'AgrCod', 'GruCod', 'SubCod', 'GbaCod')
            self.df_GbaInfo = self.df_GbaInfo.astype(dict.fromkeys(columnas, "int64"))
            # indices por divicion
            self.df_DivInd = pd.read_sql(
                f'SELECT RegCod, PerAno, PerMes, DivCod, DivInd FROM IPCPH1 WHERE PerSem=3',
                self.__conexion
            )
            self.df_DivInd = self.df_DivInd.astype({"RegCod": "int64", "DivCod": "int64"})
            # indices por gasto basico
            self.df_GbaInd = pd.read_sql(
                f'SELECT RegCod, PerAno, PerMes, DivCod, AgrCod, GruCod, SubCod, GbaCod, GbaInd FROM IPCPH5 WHERE PerAno>={self.anio - 2} AND PerSem=3',
                self.__conexion
            )
            columnas = ('RegCod', 'PerAno', 'PerMes', 'DivCod', 'AgrCod', 'GruCod', 'SubCod', 'GbaCod')
            for columna in columnas:
                self.df_GbaInd[columna] = self.df_GbaInd[columna].astype('int64')

            self.df_Fnt = fuentes.boletas_ultimos_12_meses(self.anio, self.mes)
            # Comprobamos si la carpeta db_b existe
            if not os.path.exists("db_b"):
                # Si no existe, la creamos
                os.makedirs("db_b")
            # Guardar los dataframes en la carpeta "db_b"
            self.__codex.guardar_df(self.df_DivInd, 'db_b/df_DivInd.parquet')
            self.__codex.guardar_df(self.df_DivPon, 'db_b/df_DivPon.parquet')
            self.__codex.guardar_df(self.df_GbaInd, 'db_b/df_GbaInd.parquet')
            self.__codex.guardar_df(self.df_GbaPon, 'db_b/df_GbaPon.parquet')
            self.__codex.guardar_df(self.df_GbaInfo, 'db_b/df_GbaInfo.parquet')
            self.__codex.guardar_df(self.df_DivNom, 'db_b/df_DivNom.parquet')
            self.__codex.guardar_df(self.df_Fnt, 'db_b/df_Fnt.parquet')
            # Obtener la marca temporal actual
            now = datetime.datetime.now()
            # Crear el nombre del archivo con la marca temporal
            # Crear el archivo en la carpeta "db_b" con la marca temporal como nombre
            with open('db_b/marca_temporal.txt', 'w') as file:
                file.write('Backup creado el ' + now.strftime("%d-%m-%Y %H:%M"))
        # fin de carga de datos 
        # nombre de divisiones
        abr_diviciones = {
            'Alimentos Y Bebidas No Alcohólicas': 'Alimentos',
            'Bebidas Alcohólicas Y Tabaco':'Bebidas Alcohólicas',
            'Prendas De Vestir Y Calzado':'Vestuario',
            'Vivienda, Agua, Electricidad, Gas Y Otros Combustibles':'Vivienda',
            'Muebles, Artículos Para El Hogar Y Para La Conservación  Del Hogar':'Muebles',
            'Salud':'Salud',
            'Transporte':'Transporte',
            'Comunicaciones':'Comunicaciones',
            'Recreación Y Cultura':'Recreación',
            'Educación':'Educación',
            'Restaurantes Y Hoteles':'Restaurantes',
            'Bienes Y Servicios Diversos':'Bienes diversos'
        }
        df_DivNom_dic = self.df_DivNom.to_dict()
        self.NOMBRE_DIV = dict(zip(
            [int(i) for i in df_DivNom_dic['DivCod'].values()],
            [abr_diviciones[nombre.strip().title()] for nombre in df_DivNom_dic['DivNom'].values()]
        ))

    def get_nombre_Gba(self, GbaCod: int) -> str:
        """
        Obtiene el nombre del gasto básico correspondiente al código proporcionado.

        Parameters
        ----------
        GbaCod : int
            Código del gasto básico para el cual se desea obtener el nombre.

        Returns
        -------
        str
            Nombre del gasto básico correspondiente al código proporcionado,
            con espacios iniciales y finales eliminados y en formato título.
        """
        nombre = self.df_GbaInfo[self.df_GbaInfo['GbaCod'] == GbaCod]['GbaNom'].iloc[0]
        return nombre.strip().title()

    def calcular_IPC(self, anio: int, mes: int, RegCod: int) -> float:
        """
        Calcula el índice de precios al consumidor (IPC) para una región y período de tiempo dados.

        Parameters
        ----------
        anio : int
            Año para el cual se desea calcular el IPC.
        mes : int
            Mes (número entero entre 1 y 12) para el cual se desea calcular el IPC.
        RegCod : int
            Código de la región para la cual se desea calcular el IPC.

        Returns
        -------
        float
            IPC calculado para la región y período de tiempo dados.
        """
        PONDERACIONES_REG = self.df_DivPon[self.df_DivPon['RegCod'] == RegCod]['DivPon']
        Qanio = self.df_DivInd['PerAno'] == anio
        Qmes = self.df_DivInd['PerMes'] == mes
        Qreg = self.df_DivInd['RegCod'] == RegCod
        indices = self.df_DivInd[Qanio & Qmes & Qreg]['DivInd']
        return np.average(a=indices, weights=PONDERACIONES_REG)

    def inflacion_mensual(self, anio: int, mes: int, RegCod: int) -> float:
        """
        Calcula la inflación mensual para una región específica.
        
        Parameters
        ----------
        anio : int
            El año para el cual se desea calcular la inflación.
        mes : int
            El mes para el cual se desea calcular la inflación, en formato numérico (1-12).
        RegCod : int
            El código de la región para la cual se desea calcular la inflación.
        
        Returns
        -------
        float
            El valor de la inflación mensual para la región y el periodo especificados, expresado como un porcentaje.
        """
        actual = self.calcular_IPC(anio, mes, RegCod)
        if mes == 1:
            anterior = self.calcular_IPC(anio - 1, 12, RegCod)
        else:
            anterior = self.calcular_IPC(anio, mes - 1, RegCod)
        return 100*(actual/anterior - 1)

    def inflacion_interanual(self, anio: int, mes: int, RegCod: int) -> float:
        """
        Calcula la inflación interanual para una región específica.
        
        Parameters
        ----------
        anio : int
            El año para el cual se desea calcular la inflación.
        mes : int
            El mes para el cual se desea calcular la inflación, en formato numérico (1-12).
        RegCod : int
            El código de la región para la cual se desea calcular la inflación.
        
        Returns
        -------
        float
            El valor de la inflación interanual para la región y el periodo especificados, expresado como un porcentaje.
        """
        actual = self.calcular_IPC(anio, mes, RegCod)
        anterior = self.calcular_IPC(anio - 1, mes, RegCod)
        return 100*(actual/anterior - 1)
    
    def inflacion_acumulada(self, anio: int, mes: int, RegCod: int) -> float:
        """
        Calcula la inflación acumulada para una región específica.
        
        Parameters
        ----------
        anio : int
            El año para el cual se desea calcular la inflación acumulada.
        mes : int
            El mes para el cual se desea calcular la inflación acumulada, en formato numérico (1-12).
        RegCod : int
            El código de la región para la cual se desea calcular la inflación acumulada.
        
        Returns
        -------
        float
            El valor de la inflación acumulada para la región y el periodo especificados, expresado como un porcentaje.
        """
        actual = self.calcular_IPC(anio, mes, RegCod)
        anterior = self.calcular_IPC(anio - 1, 12, RegCod)
        return 100*(actual/anterior - 1)
    
    def poder_adquisitivo(self, anio: int, mes: int, RegCod: int) -> float:
        """
        Calcula el poder adquisitivo de la moneda para una región específica.
        
        Parameters
        ----------
        anio : int
            El año para el cual se desea calcular el poder adquisitivo.
        mes : int
            El mes para el cual se desea calcular el poder adquisitivo, en formato numérico (1-12).
        RegCod : int
            El código de la región para la cual se desea calcular el poder adquisitivo.
        
        Returns
        -------
        float
            El valor del poder adquisitivo de la moneda para la región y el periodo especificados, expresado como un porcentaje.
        """
        return (1 / self.calcular_IPC(anio, mes, RegCod)) * 100

    def incidencia_divisiones(self, RegCod: int) -> List[float]:
        """
        Calcula la incidencia de cada división en el índice de precios al consumidor
        en una determinada región y periodo.

        Args:
            RegCod (int): Código de la región.

        Returns:
            List[float]: Lista de tuplas que contiene la incidencia de cada división 
            en el índice de precios al consumidor de la región, en orden descendente. 
            Cada tupla contiene la variación ponderada de la división y su nombre.
        """
        incidencias = []
        for DivCod in range(1, 13):
            ponderacion = self.df_DivPon[(self.df_DivPon['RegCod'] == RegCod) & (self.df_DivPon['DivCod'] == DivCod)]['DivPon'].iloc[0]
            Qanio = self.df_DivInd['PerAno'] == self.anio
            Qmes = self.df_DivInd['PerMes'] == self.mes
            Qreg = self.df_DivInd['RegCod'] == RegCod
            Qdiv = self.df_DivInd['DivCod'] == DivCod
            indice_actual = self.df_DivInd[Qanio & Qmes & Qreg & Qdiv]['DivInd'].iloc[0]
            if self.mes == 1:
                Qanio = self.df_DivInd['PerAno'] == self.anio - 1
                Qmes = self.df_DivInd['PerMes'] == 12
                ipc_anterior = self.calcular_IPC(self.anio - 1, 12, RegCod)
            else:
                Qmes = self.df_DivInd['PerMes'] == self.mes - 1
                ipc_anterior = self.calcular_IPC(self.anio, self.mes - 1, RegCod)
            indice_anterior = self.df_DivInd[Qanio & Qmes & Qreg & Qdiv]['DivInd'].iloc[0]
            variacion = ((indice_actual - indice_anterior) / ipc_anterior) * ponderacion
            variacion = r0und(variacion, 2)
            incidencias.append((variacion, self.NOMBRE_DIV[DivCod]))
        return incidencias

    def incidencia_gasto_basico(self, RegCod: int) -> List[Tuple[float, str]]:
        """
        Obtiene la incidencia de la variación de los gastos básicos para una región.

        Parámetros:
        -----------
        - RegCod: int. Código de la región de interés.

        Retorna:
        --------
        - List[Tuple[float, str]]: Lista de tuplas que contienen la incidencia de la variación de los gastos básicos
        y su nombre correspondiente para la región de interés.
        """
        incidencias = []
        for GbaCod in self.df_GbaInfo['GbaCod'].to_list():
            ponderacion = self.df_GbaPon[(self.df_GbaPon['RegCod'] == RegCod) & (self.df_GbaPon['GbaCod'] == GbaCod)]['GbaPon'].iloc[0]
            Qanio = self.df_GbaInd['PerAno'] == self.anio
            Qmes = self.df_GbaInd['PerMes'] == self.mes
            Qreg = self.df_GbaInd['RegCod'] == RegCod
            Qgba = self.df_GbaInd['GbaCod'] == GbaCod
            try:
                indice_actual = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba]['GbaInd'].iloc[0]
            except:
                pass
            if self.mes == 1:
                Qanio = self.df_GbaInd['PerAno'] == self.anio - 1
                Qmes = self.df_GbaInd['PerMes'] == 12
                ipc_anterior = self.calcular_IPC(self.anio - 1, 12, RegCod)
            else:
                Qmes = self.df_GbaInd['PerMes'] == self.mes - 1
                ipc_anterior = self.calcular_IPC(self.anio, self.mes - 1, RegCod)
            try:
                indice_anterior = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba]['GbaInd'].iloc[0]
            except:
                pass
            variacion = ((indice_actual - indice_anterior) / ipc_anterior) * ponderacion
            nombre_gba = self.get_nombre_Gba(GbaCod)
            incidencias.append((variacion, nombre_gba))
        return incidencias

    def series_historicas_Gbas(self, RegCod: int) -> List[Tuple[str, List[Tuple[str, float]]]]:
        """
        Devuelve una lista de tuplas, cada una representando una serie histórica
        de un gasto básico diferente. La tupla contiene el nombre del gasto básico
        y una lista de tuplas que contienen la fecha en formato "mes-año" y el
        índice correspondiente a ese mes y año.

        Parámetros:
        -----------
        RegCod: int
            Código de región.

        Returns:
        --------
        series: List[Tuple[str, List[Tuple[str, float]]]]
            Lista de tuplas que contienen el nombre del gasto básico y la lista de
            tuplas de fecha-índice correspondientes a ese gasto básico.
        """
        series = []
        for GbaCod in self.df_GbaInfo['GbaCod'].to_list():
            if self.mes != 12:
                Qanio = self.df_GbaInd['PerAno'] == self.anio
                Qmes = self.df_GbaInd['PerMes'] <= self.mes
                Qreg = self.df_GbaInd['RegCod'] == RegCod
                Qgba = self.df_GbaInd['GbaCod'] == GbaCod
                #Qsem = self.df_GbaInd['PerSem'] == 3
                indices1 = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba][['PerAno','PerMes','GbaInd']]
                Qanio = self.df_GbaInd['PerAno'] == self.anio - 1
                Qmes = self.df_GbaInd['PerMes'] >= self.mes
                indices2 = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba][['PerAno','PerMes','GbaInd']]
                indices = pd.merge(indices2, indices1, how='outer')
            else:
                Qanio = self.df_GbaInd['PerAno'] == self.anio
                Qmes = self.df_GbaInd['PerMes'] <= self.mes
                Qreg = self.df_GbaInd['RegCod'] == RegCod
                Qgba = self.df_GbaInd['GbaCod'] == GbaCod
                #Qsem = self.df_GbaInd['PerSem'] == 3
                indices = self.df_GbaInd[Qanio & Qmes & Qreg & Qgba][['PerAno','PerMes','GbaInd']]
            nombre_gba = self.get_nombre_Gba(GbaCod)
            indices_final = []
            indices = indices.sort_values(by=['PerAno', 'PerMes'])
            if len(indices) != 0:
                for i in range(len(indices)):
                    mes_abr = mes_by_ordinal(indices['PerMes'].iat[i])
                    anio = indices['PerAno'].iat[i]
                    fecha = f'{mes_abr}-{anio}'
                    indice = indices['GbaInd'].iat[i]
                    indices_final.append((fecha, indice))
                series.append((nombre_gba, indices_final))
        return series

    def serie_historica_ipc_pdr_adq(self, RegCod: int, Qpdr_adq: bool=False):
        """
        Retorna una serie histórica del IPC para una región específica.

        Args:
            RegCod (int): Código de la región para la cual se quiere obtener la
            serie histórica del IPC.
            Qpdr_adq (bool, optional): Indica si se quiere calcular la serie
            histórica en términos de poder adquisitivo o no. Por defecto es False.

        Returns:
            List[Tuple[str, float]]: Lista de tuplas, donde cada tupla contiene
            dos elementos: la fecha en formato "mes-año" y el valor del IPC
            correspondiente a esa fecha.
        """
        serie = []
        if Qpdr_adq:
            funcion = self.poder_adquisitivo
        else:
            funcion = self.calcular_IPC
        if self.mes != 12:
            for i in range(self.mes, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio - 1}'
                ipc = funcion(self.anio - 1, i, RegCod)
                serie.append((fecha, ipc))
            for i in range(1, self.mes + 1):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                ipc = funcion(self.anio, i, RegCod)
                serie.append((fecha, ipc))
        else:
            for i in range(1, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                ipc = funcion(self.anio, i, RegCod)
                serie.append((fecha, ipc))
        return serie

    def serie_historica_inflacion(self, RegCod: int, tipo: str) -> List[Tuple[str, float]]:
        """
        Retorna una serie histórica de inflación para una región específica.

        Args:
            RegCod (int): Código de la región para la cual se quiere obtener la
            serie histórica de inflación.
            tipo (str): Tipo de inflación que se desea calcular. Puede ser
            'intermensual', 'interanual' o 'acumulada'.

        Returns:
            List[Tuple[str, float]]: Lista de tuplas, donde cada tupla contiene
            dos elementos: la fecha en formato "mes-año" y el valor del índice
            de inflación correspondiente a esa fecha.
        """
        serie = []
        if tipo == 'intermensual':
            funcion = self.inflacion_mensual
        elif tipo == 'interanual':
            funcion = self.inflacion_interanual
        elif tipo == 'acumulada':
            funcion = self.inflacion_acumulada
        if tipo == 'acumulada':
            for anio in range(2012, self.anio + 1):
                mes_abr = mes_by_ordinal(self.mes)
                fecha = f'{mes_abr}-{anio}'
                indice = funcion(anio, self.mes, RegCod)
                serie.append((fecha, indice))
        else:
            if self.mes != 12:
                for i in range(self.mes, 13):
                    mes_abr = mes_by_ordinal(i)
                    fecha = f'{mes_abr}-{self.anio - 1}'
                    indice = funcion(self.anio - 1, i, RegCod)
                    serie.append((fecha, indice))
                for i in range(1, self.mes + 1):
                    mes_abr = mes_by_ordinal(i)
                    fecha = f'{mes_abr}-{self.anio}'
                    indice = funcion(self.anio, i, RegCod)
                    serie.append((fecha, indice))
            else:
                for i in range(1, 13):
                    mes_abr = mes_by_ordinal(i)
                    fecha = f'{mes_abr}-{self.anio}'
                    indice = funcion(self.anio, i, RegCod)
                    serie.append((fecha, indice))
        return serie

    def serie_fuentes_precios(self, Qfuentes: bool = True, RegCod: int = 0) -> List[Tuple[str, int]]:
        """
        Devuelve una serie histórica con la cantidad de fuentes de precios disponibles
        para cada mes y año.
        
        Parameters
        ----------
        Qfuentes : bool, optional
            Si es True, se contabilizan solamente las fuentes de precios únicas (eliminando duplicados), 
            de lo contrario, se cuentan todas las observaciones. Por defecto es True.
            
        Returns
        -------
        List[Tuple[str, int]]
            Lista de tuplas con la información de la serie histórica. 
            Cada tupla contiene dos elementos: 
            - un string con la fecha en formato 'Abr-Año'
            - un entero con la cantidad de fuentes de precios disponibles para esa fecha.
        """
        serie = []
        if self.mes != 12:
            for i in range(self.mes, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio - 1}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio - 1
                conteo = self.df_Fnt[anio_ & mes_]
                if RegCod != 0:
                    conteo = conteo[conteo['RegCod'] == RegCod]
                if Qfuentes:
                    conteo = conteo.drop_duplicates(subset=["DepCod", "MunCod", "FntCod"])
                serie.append((fecha, conteo.shape[0]))
            for i in range(1, self.mes + 1):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio
                conteo = self.df_Fnt[anio_ & mes_]
                if RegCod != 0:
                    conteo = conteo[conteo['RegCod'] == RegCod]
                if Qfuentes:
                    conteo = conteo.drop_duplicates(subset=["DepCod", "MunCod", "FntCod"])
                serie.append((fecha, conteo.shape[0]))
        else:
            for i in range(1, 13):
                mes_abr = mes_by_ordinal(i)
                fecha = f'{mes_abr}-{self.anio}'
                mes_ = self.df_Fnt['PerMes'] == i
                anio_ = self.df_Fnt['PerAno'] == self.anio
                conteo = self.df_Fnt[anio_ & mes_]
                if RegCod != 0:
                    conteo = conteo[conteo['RegCod'] == RegCod]
                if Qfuentes:
                    conteo = conteo.drop_duplicates(subset=["DepCod", "MunCod", "FntCod"])
                serie.append((fecha, conteo.shape[0]))
        return serie

    def desagregacion_fuentes(self) -> List[Tuple[str, int]]:
        """
        Desagrega el número de fuentes por tipo de fuente.

        Returns:
        -----------
        List[Tuple[str, int]]:
            Una lista de tuplas que contienen el nombre del tipo de fuente y el número de fuentes para el mes y año actual.
        """
        serie = []
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        S = 1
        for i in range(24):
            if i in (17,18,19): # no existen estos tipos de fuentes
                continue
            tipo_fuente_ = self.df_Fnt['TfnCod'] == str(i).zfill(2)
            conteo = self.df_Fnt[anio_ & mes_ & tipo_fuente_].drop_duplicates(subset=["DepCod", "MunCod", "FntCod"]).shape[0]
            S += conteo
            nmbr_Fnt = self.nombre_fuentes.get(i)
            serie.append((nmbr_Fnt, conteo))
        invertir = [(i[1] / S * 100, i[0]) for i in serie]
        serie = [i[::-1] for i in sorted(invertir, reverse=True)]
        # hacer pareto
        acumulado = 0
        for i, fuente in enumerate(serie):
            acumulado += fuente[1]
            if acumulado >= 80:
                break
        return serie[0:i + 1]
    
    def desagregacion_fuentes_cantidad(self) -> List[Tuple[str, int]]:
        """
        Desagrega el número de fuentes por tipo de fuente.

        Returns:
        -----------
        List[Tuple[str, int]]:
            Una lista de tuplas que contienen el nombre del tipo de fuente y el número de fuentes para el mes y año actual.
        """
        serie = []
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        S = 1
        for i in range(24):
            if i in (17,18,19): # no existen estos tipos de fuentes
                continue
            tipo_fuente_ = self.df_Fnt['TfnCod'] == str(i).zfill(2)
            conteo = self.df_Fnt[anio_ & mes_ & tipo_fuente_].drop_duplicates(subset=["DepCod", "MunCod", "FntCod"]).shape[0]
            S += conteo
            nmbr_Fnt = self.nombre_fuentes.get(i)
            serie.append((nmbr_Fnt, conteo))
        invertir = [(i[1] , i[0]) for i in serie]
        serie = [i[::-1] for i in sorted(invertir, reverse=True)]
        # hacer pareto
        acumulado = 0
        for i, fuente in enumerate(serie):
            acumulado += fuente[1]
            if acumulado >= 80:
                break
        return serie

    def cobertura_fuentes_precios(self, Qfuentes: bool = True) -> List[Tuple[int, int]]:
        """Calcula la cobertura de fuentes de precios para cada región en un mes y año específico.

        Args:
            Qfuentes (bool, optional): Si se requiere el conteo de fuentes únicas. Defaults to True.

        Returns:
            List[Tuple[int, int]]: Una lista de tuplas que contiene el código de región y el número de fuentes 
            de precios para la región especificada en el mes y año específico.
        """
        cobertura = []
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        for i in range(1, 9):
            RegCod_ = self.df_Fnt['RegCod'] == i
            conteo = self.df_Fnt[anio_ & mes_ & RegCod_]
            if Qfuentes:
                conteo = conteo.drop_duplicates(subset=["DepCod", "MunCod", "FntCod"])
            cobertura.append((i, conteo.shape[0]))
        return cobertura

    def serie_historica(self, tipo: str) -> List[Tuple[str, float]]:
        serie = []
        if tipo == 'mensual':
            funcion = self.inflacion_mensual
        elif tipo == 'anual':
            funcion = self.inflacion_interanual
        elif tipo == 'IPC':
            funcion = self.calcular_IPC
        if tipo != 'anual':
            anio_inf = 2011
        else:
            anio_inf = 2012
        for anio in range(anio_inf, self.anio):
            mes_inf = 4 if anio == anio_inf else 1
            for mes in range(mes_inf, 13):
                indice = funcion(anio, mes, 0)
                mes_abr = mes_by_ordinal(mes)
                fecha = f'{mes_abr}-{anio}'
                serie.append((fecha, indice))
        for mes in range(1, self.mes + 1):
                indice = funcion(self.anio, mes, 0)
                mes_abr = mes_by_ordinal(mes)
                fecha = f'{mes_abr}-{self.anio}'
                serie.append((fecha, indice))
        return serie

    def serie_historica_mensual_inflacion(self, RegCod: int, tipo: str) -> List[Tuple[str, float]]:
        """
        Retorna una serie histórica de inflación para una región específica.

        Args:
            RegCod (int): Código de la región para la cual se quiere obtener la
            serie histórica de inflación.
            tipo (str): Tipo de inflación que se desea calcular. Puede ser
            'intermensual', 'interanual' o 'acumulada'.

        Returns:
            List[Tuple[str, float]]: Lista de tuplas, donde cada tupla contiene
            dos elementos: la fecha en formato "mes-año" y el valor del índice
            de inflación correspondiente a esa fecha.
        """
        serie = []
        if tipo == 'intermensual':
            funcion = self.inflacion_mensual
        elif tipo == 'interanual':
            funcion = self.inflacion_interanual
        elif tipo == 'acumulada':
            funcion = self.inflacion_acumulada

        for anio in range(2012, self.anio + 1):
            mes_abr = mes_by_ordinal(self.mes)
            fecha = f'{mes_abr}-{anio}'
            indice = funcion(anio, self.mes, RegCod)
            serie.append((fecha, indice))
        return serie
    
    def deteccion_Fnt_sin_tipo(self):
        mes_ = self.df_Fnt['PerMes'] == self.mes
        anio_ = self.df_Fnt['PerAno'] == self.anio
        tipo_fuente = 0

        tipo_fuente_ = self.df_Fnt['TfnCod'] == str(tipo_fuente).zfill(2)
        sin_fuente = self.df_Fnt[anio_ & mes_ & tipo_fuente_].drop_duplicates(subset=["DepCod", "MunCod", "FntCod"])

        nmbr_Fnt = self.nombre_fuentes.get(tipo_fuente)

        return (sin_fuente, nmbr_Fnt)

SqlIPC(2023, 6)