"""Validated historical sales analytics for San Francisco Crust Pizza."""
import pandas as pd

REQUIRED = {
    'ventas': {'VentaID','Fecha','Ciudad','Sucursal','ClienteID','ProductoID','Cantidad','VentaNeta','CostoTotal','UtilidadBruta'},
    'clientes': {'ClienteID','Segmento'},
    'productos': {'ProductoID','Producto','Categoria'},
}

def load_file(source, name=None):
    name = name or getattr(source,'name',str(source))
    return pd.read_csv(source) if str(name).lower().endswith('.csv') else pd.read_excel(source)

def prepare(ventas, clientes, productos):
    for name, frame in [('ventas',ventas),('clientes',clientes),('productos',productos)]:
        missing=REQUIRED[name]-set(frame.columns)
        if missing: raise ValueError(f'{name}: faltan columnas: {", ".join(sorted(missing))}')
        if frame.empty: raise ValueError(f'{name}: archivo vacío')
    for name,frame,key in [('clientes',clientes,'ClienteID'),('productos',productos,'ProductoID')]:
        if frame[key].isna().any() or frame[key].duplicated().any():
            raise ValueError(f'{name}: {key} contiene duplicados o valores vacíos')
    if ventas['VentaID'].isna().any(): raise ValueError('Ventas: hay VentaID vacíos')
    v=ventas.copy()
    v['Fecha']=pd.to_datetime(v['Fecha'],errors='coerce')
    if v['Fecha'].isna().any(): raise ValueError('Ventas: fechas inválidas')
    for col in ['Cantidad','VentaNeta','CostoTotal','UtilidadBruta']:
        v[col]=pd.to_numeric(v[col],errors='coerce')
        if v[col].isna().any(): raise ValueError(f'Ventas: valores no numéricos en {col}')
    if (v['Cantidad']<0).any() or (v['CostoTotal']<0).any():
        raise ValueError('Ventas: cantidades o costos negativos')
    if v.duplicated().any(): raise ValueError('Ventas: filas completamente duplicadas; revisar archivo antes de continuar')
    v=v.merge(clientes[['ClienteID','Segmento']],on='ClienteID',how='left',validate='many_to_one',indicator='_cliente_match')
    v=v.merge(productos[['ProductoID','Producto','Categoria']],on='ProductoID',how='left',validate='many_to_one',indicator='_producto_match')
    missing_clients=int((v['_cliente_match']!='both').sum())
    missing_products=int((v['_producto_match']!='both').sum())
    if missing_clients or missing_products:
        raise ValueError(f'Relaciones inválidas: {missing_clients} ventas sin cliente; {missing_products} ventas sin producto. Cargá también los catálogos actualizados.')
    v=v.drop(columns=['_cliente_match','_producto_match'])
    v['MesPeriodo']=v['Fecha'].dt.to_period('M').astype(str)
    return v

def kpis(df):
    revenue=float(df['VentaNeta'].sum()); profit=float(df['UtilidadBruta'].sum())
    n=int(df['VentaID'].nunique())
    return {'ventas':revenue,'utilidad':profit,'margen':profit/revenue if revenue else None,
            'ticket':revenue/n if n else None,'clientes':int(df['ClienteID'].nunique()),'transacciones':n,
            'unidades':float(df['Cantidad'].sum())}

def aggregate(df,field):
    result=df.groupby(field,dropna=False).agg(ventas=('VentaNeta','sum'),utilidad=('UtilidadBruta','sum'),
                    transacciones=('VentaID','nunique'),clientes=('ClienteID','nunique'),unidades=('Cantidad','sum')).reset_index()
    result['margen']=result['utilidad'].div(result['ventas'].where(result['ventas']!=0))
    return result

def summary(df):
    branch=aggregate(df,'Sucursal').sort_values('ventas',ascending=False)
    prod=aggregate(df,'Producto').sort_values('utilidad',ascending=False)
    seg=aggregate(df,'Segmento').sort_values('ventas',ascending=False)
    return {'kpis':kpis(df),'sucursales':branch.head(20).round(3).to_dict('records'),
            'productos':prod.head(20).round(3).to_dict('records'),
            'segmentos':seg.head(20).round(3).to_dict('records')}
