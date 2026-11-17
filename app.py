import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from analytics import load_file, prepare, kpis, aggregate, summary

st.set_page_config(page_title='San Francisco Crust Pizza | BI',page_icon='🍕',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1450px}
h1,h2,h3{color:#17335b}div[data-testid="stMetric"]{background:#f2f6fb;border:1px solid #e0e8f3;padding:16px;border-radius:13px}
</style>''',unsafe_allow_html=True)
st.title('🍕 San Francisco Crust Pizza')
st.caption('Sistema Inteligente de Apoyo a la Toma de Decisiones · UNIR · Datos oficiales del caso')
DATA=Path(__file__).parent/'data'
files={'ventas':'San_Francisco_Crust_Pizza_Ventas.xlsx','clientes':'San_Francisco_Crust_Pizza_Clientes.xlsx','productos':'San_Francisco_Crust_Pizza_Productos.xlsx'}
st.sidebar.header('Fuentes de información')
st.sidebar.caption('Las nuevas bases sustituyen los datos de la sesión. Para guardar cambios permanentemente, actualizá los archivos del servidor.')
new={}
for key in files:
    new[key]=st.sidebar.file_uploader(f'Actualizar {key}',type=['xlsx','csv'],key=f'upload_{key}')
@st.cache_data(show_spinner='Leyendo datos...')
def cached_default(name): return load_file(DATA/name)
try:
    frames={key:load_file(new[key],new[key].name) if new[key] is not None else cached_default(filename) for key,filename in files.items()}
    data=prepare(frames['ventas'],frames['clientes'],frames['productos'])
except Exception as exc:
    st.error(f'No se pueden procesar los datos: {exc}')
    st.info('Revisá las columnas y relaciones de los archivos. Los nuevos archivos deben mantener el esquema de los originales.')
    st.stop()
st.sidebar.success(f'{len(data):,} registros cargados')
st.sidebar.header('Filtros globales')
minimum=data['Fecha'].min().date(); maximum=data['Fecha'].max().date()
period=st.sidebar.date_input('Fecha',value=(minimum,maximum),min_value=minimum,max_value=maximum)
if not isinstance(period,(tuple,list)) or len(period)!=2:
    st.info('Seleccioná las dos fechas del período.'); st.stop()
filtered=data.loc[data['Fecha'].dt.date.between(period[0],period[1])].copy()
for col,label in [('Ciudad','Ciudad'),('Sucursal','Sucursal'),('Segmento','Segmento de cliente'),('Producto','Producto')]:
    options=sorted(filtered[col].dropna().astype(str).unique().tolist())
    selected=st.sidebar.multiselect(label,options,key=f'filter_{col}')
    if selected: filtered=filtered[filtered[col].isin(selected)]
if st.sidebar.button('Restablecer filtros'):
    for col in ['Ciudad','Sucursal','Segmento','Producto']: st.session_state[f'filter_{col}']=[]
    st.rerun()
if filtered.empty:
    st.warning('No hay ventas con los filtros seleccionados.'); st.stop()
metrics=kpis(filtered)
fmt=lambda x:f'${x:,.0f}'
for col,(label,val) in zip(st.columns(6),[
    ('Ventas totales',fmt(metrics['ventas'])),('Utilidad bruta',fmt(metrics['utilidad'])),
    ('Margen bruto',f"{metrics['margen']:.1%}" if metrics['margen'] is not None else 'N/D'),
    ('Ticket promedio',f"${metrics['ticket']:,.2f}" if metrics['ticket'] is not None else 'N/D'),
    ('Clientes',f"{metrics['clientes']:,}"),('Transacciones',f"{metrics['transacciones']:,}")]): col.metric(label,val)
st.caption('Cálculos basados en VentaNeta, CostoTotal y UtilidadBruta históricos. Ticket promedio = ventas netas / VentaID únicos.')
px.defaults.template='plotly_white'
def chart(fig):
    fig.update_layout(margin=dict(l=15,r=15,t=55,b=20),font=dict(size=13),legend_title_text='')
    st.plotly_chart(fig,use_container_width=True)

tabs=st.tabs(['📊 Resumen ejecutivo','🍕 Productos','🏬 Sucursales y ciudades','👥 Clientes','🤖 Asistente IA','📁 Datos y calidad'])
with tabs[0]:
    monthly=filtered.groupby('MesPeriodo',as_index=False)[['VentaNeta','UtilidadBruta']].sum()
    chart(px.line(monthly,x='MesPeriodo',y=['VentaNeta','UtilidadBruta'],markers=True,
        labels={'MesPeriodo':'Mes','value':'USD','variable':'Indicador'},title='Evolución mensual de ventas y utilidad'))
    left,right=st.columns(2)
    with left:
        city=aggregate(filtered,'Ciudad').sort_values('ventas',ascending=False)
        chart(px.bar(city,x='Ciudad',y='ventas',title='Ventas por ciudad',labels={'ventas':'USD'}))
    with right:
        branch=aggregate(filtered,'Sucursal').sort_values('ventas',ascending=False)
        chart(px.bar(branch,x='ventas',y='Sucursal',orientation='h',title='Ventas por sucursal',labels={'ventas':'USD'}))
    top=aggregate(filtered,'Producto').nlargest(10,'unidades').sort_values('unidades')
    chart(px.bar(top,x='unidades',y='Producto',orientation='h',title='Top 10 productos más vendidos (unidades)'))
with tabs[1]:
    p=aggregate(filtered,'Producto').sort_values('utilidad',ascending=False)
    a,b=st.columns(2)
    with a: chart(px.bar(p.head(15).sort_values('utilidad'),x='utilidad',y='Producto',orientation='h',title='Productos con mayor utilidad bruta'))
    with b: chart(px.bar(p.sort_values('margen',ascending=False).head(15).sort_values('margen'),x='margen',y='Producto',orientation='h',title='Productos con mayor margen bruto',labels={'margen':'Margen'}))
    st.dataframe(p.style.format({'ventas':'${:,.2f}','utilidad':'${:,.2f}','margen':'{:.1%}'}),use_container_width=True,hide_index=True)
with tabs[2]:
    branches=aggregate(filtered,'Sucursal').sort_values('ventas',ascending=False)
    branches['ticket']=branches['ventas']/branches['transacciones'].replace(0,float('nan'))
    chart(px.scatter(branches,x='ventas',y='margen',size='transacciones',hover_name='Sucursal',title='Sucursales: ventas vs margen (tamaño = transacciones)',labels={'ventas':'Ventas USD','margen':'Margen bruto'}))
    st.dataframe(branches.style.format({'ventas':'${:,.2f}','utilidad':'${:,.2f}','margen':'{:.1%}','ticket':'${:,.2f}'}),use_container_width=True,hide_index=True)
    city=aggregate(filtered,'Ciudad').sort_values('ventas',ascending=False)
    st.subheader('Comparación de ciudades')
    st.dataframe(city.style.format({'ventas':'${:,.2f}','utilidad':'${:,.2f}','margen':'{:.1%}'}),use_container_width=True,hide_index=True)
with tabs[3]:
    segment=aggregate(filtered,'Segmento').sort_values('ventas',ascending=False)
    a,b=st.columns(2)
    with a: chart(px.bar(segment,x='Segmento',y='ventas',title='Ventas por segmento'))
    with b: chart(px.bar(segment,x='Segmento',y='clientes',title='Clientes compradores por segmento'))
    st.dataframe(segment.style.format({'ventas':'${:,.2f}','utilidad':'${:,.2f}','margen':'{:.1%}'}),use_container_width=True,hide_index=True)
    st.caption('Los clientes representan compradores únicos del período filtrado, no toda la cartera registrada.')
with tabs[4]:
    st.subheader('Asistente inteligente comercial')
    context=summary(filtered)
    st.caption('Las recomendaciones deben basarse en los datos filtrados. Contrastá cualquier propuesta con las tablas y gráficos.')
    st.download_button('Descargar contexto analítico (JSON)',json.dumps(context,ensure_ascii=False,indent=2).encode('utf-8'),file_name='contexto_ia.json',mime='application/json')
    st.markdown('**Hallazgos automáticos (reglas analíticas, no IA generativa)**')
    branch=aggregate(filtered,'Sucursal').sort_values('ventas',ascending=False)
    prod=aggregate(filtered,'Producto').sort_values('utilidad',ascending=False)
    seg=aggregate(filtered,'Segmento').sort_values('ventas',ascending=False)
    st.write(f"• Mayor venta por sucursal: **{branch.iloc[0]['Sucursal']}** (${branch.iloc[0]['ventas']:,.2f}).")
    st.write(f"• Menor venta por sucursal: **{branch.iloc[-1]['Sucursal']}** (${branch.iloc[-1]['ventas']:,.2f}).")
    st.write(f"• Mayor utilidad por producto: **{prod.iloc[0]['Producto']}** (${prod.iloc[0]['utilidad']:,.2f}).")
    st.write(f"• Segmento con mayores ventas: **{seg.iloc[0]['Segmento']}** (${seg.iloc[0]['ventas']:,.2f}).")
    st.info('La sección siguiente utiliza IA generativa solo cuando se configura una clave API. Los hallazgos anteriores son cálculos determinísticos.')
    api_key=None
    try: api_key=st.secrets.get('OPENAI_API_KEY')
    except Exception: pass
    if not api_key: api_key=st.text_input('Clave API (opcional; solo para esta sesión)',type='password')
    question=st.text_area('Pregunta al asistente',value='Identifica cinco decisiones estratégicas, con cifras de soporte y riesgos, a partir de los datos filtrados.')
    if st.button('Generar recomendaciones con IA',disabled=not bool(api_key)):
        try:
            from openai import OpenAI
            client=OpenAI(api_key=api_key)
            response=client.responses.create(model='gpt-4.1-mini',instructions=('Eres un analista comercial. Responde en español. Usa exclusivamente el JSON de datos proporcionado para afirmaciones cuantitativas. No inventes cifras ni causas. Distingue evidencia, hipótesis, recomendación, riesgos y KPIs. Si faltan datos dilo.'),input=f'Pregunta: {question}\nContexto: {json.dumps(context,ensure_ascii=False)}')
            st.markdown(response.output_text)
        except Exception as exc: st.error(f'No fue posible consultar el modelo: {exc}')
    if not api_key: st.caption('Para activar IA generativa, ingresá una clave API válida o configurá OPENAI_API_KEY en los secretos de Streamlit. La API puede generar costos.')
with tabs[5]:
    st.subheader('Control de calidad y actualización')
    st.write(f"**Filas filtradas:** {len(filtered):,} · **Transacciones únicas:** {metrics['transacciones']:,}")
    st.write(f"**Rango:** {filtered['Fecha'].min():%Y-%m-%d} a {filtered['Fecha'].max():%Y-%m-%d}")
    delta=(filtered['VentaNeta']-filtered['CostoTotal']-filtered['UtilidadBruta']).abs()
    st.write(f'**Filas con diferencia contable > $0.02:** {(delta>0.02).sum():,}')
    st.write(f"**VentaID repetidos (líneas adicionales):** {len(filtered)-filtered['VentaID'].nunique():,}")
    st.dataframe(filtered.drop(columns=['ClienteID'],errors='ignore').head(1000),use_container_width=True,hide_index=True)
    st.download_button('Descargar datos filtrados (CSV)',filtered.to_csv(index=False).encode('utf-8-sig'),file_name='ventas_filtradas.csv',mime='text/csv')
    st.caption('Los archivos subidos se aplican a la sesión actual; el despliegue público no almacena automáticamente nuevas cargas para otros usuarios.')
