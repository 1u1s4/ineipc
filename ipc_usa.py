from fredapi import Fred
from funcionesjo import year_ago, month_after, mes_by_ordinal, hoy

fred = Fred(api_key='734b605521e7734edc09f38e977fe238')
FECHA_REPORTE = hoy("%Y-%m-01")#"2015-11-01"
FECHA_ANTERIOR = year_ago(FECHA_REPORTE)
FECHA_ANTERIOR_ANTERIOR = str(int(FECHA_REPORTE.split("-")[0]) - 2) + "-01-01"
data = fred.get_series('CPIAUCSL', observation_start=FECHA_ANTERIOR_ANTERIOR, observation_end=FECHA_REPORTE)
fecha_i = FECHA_ANTERIOR
datos_variacion_interanual = []
for i in range(13):
    try:
        precio = data.dropna().loc[fecha_i]
        precio_anterior = data.dropna().loc[year_ago(fecha_i)]
        mes_actual_i = "-".join((fecha_i.split("-")[0], mes_by_ordinal(fecha_i.split("-")[1])))
        variacion = ((precio / precio_anterior) - 1) * 100
        datos_variacion_interanual.append((mes_actual_i, variacion))
        fecha_i = month_after(fecha_i)
    except:
        pass

for i in datos_variacion_interanual:
    print(i)
