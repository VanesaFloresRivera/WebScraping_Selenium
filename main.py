#EXTRACCIÓN DE LA INFORMACIÓN CON SELENIUM
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException 
import pandas as pd
import time


# Configuración de Selenium WebDriver para Edge
service = Service(EdgeChromiumDriverManager().install())
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Edge(service=service, options=options)

# URL base de eBay
base_url = "https://www.ebay.es"

# Inicialización de variables
products = []
current_page = 1
search_query = "bicicleta niños"

try:
    # Abrir la página base
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # Lista de posibles selectores para el campo de búsqueda
    search_selectors = [
        "input#gh-ac",  # ID principal de búsqueda en eBay
        "input[name='_nkw']",  # Nombre alternativo del campo
        "input.search-box",  # Clase genérica de búsqueda
        "input[type='text']",  # Selector genérico
        "input[placeholder='Buscar artículos']"  # Placeholder en español
    ]

    search_box = None
    for selector in search_selectors:
        try:
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            print(f"Search box found with selector: {selector}")
            break
        except TimeoutException:
            continue

    if not search_box:
        print("Debug info:")
        print(f"Current URL: {driver.current_url}")
        print("Page source preview:", driver.page_source[:500])
        raise Exception("No se pudo encontrar el campo de búsqueda usando ningún selector conocido")

    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    while True:
        print(f"Scraping página {current_page}...")

        # Esperar a que los productos se carguen
        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".s-item"))
        )

        # Extraer información de los productos
        items = driver.find_elements(By.CSS_SELECTOR, ".s-item")
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, ".s-item__title").text
            except:
                title = None

            try:
                sub_title = item.find_element(By.CSS_SELECTOR, ".s-item__subtitle").text
            except:
                sub_title = None

            try:
                price = item.find_element(By.CSS_SELECTOR, ".s-item__price").text
            except:
                price = None

            try:
                shipping_costs = item.find_element(By.CSS_SELECTOR, ".s-item__shipping").text
            except:
                shipping_costs = None

            try:
                location = item.find_element(By.CSS_SELECTOR, ".s-item__location").text
            except:
                location = None

            try:
                sales = item.find_element(By.CSS_SELECTOR, ".s-item__hotness").text
            except:
                sales = None
            
            try:
                link_element = item.find_element(By.CLASS_NAME, "s-item__link")
                href= link_element.get_attribute("href")
            except:
                href = None
                link_element=None

            products.append({
                "Title": title,
                "Sub_title": sub_title,
                "Price": price,
                "Shipping_cost": shipping_costs,
                "Location": location,
                "Sales": sales,
                "link":href
            })

        # Intentar encontrar el botón "Siguiente"
        try:
            # Esperar a que el botón "Siguiente" esté presente y sea clickeable
            next_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination__next"))
            )
            
            if "disabled" in next_button.get_attribute("class"):
                print("Se alcanzó la última página")
                break
                
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination__next")))
            next_button.click()
            current_page += 1
            
            # Esperar a que la nueva página se cargue
            wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException as e:
            print(f"Timeout esperando el botón 'Siguiente' o la carga de la página: {str(e)}")
            break
        except Exception as e:
            print(f"Error al navegar a la siguiente página: {str(e)}")
            break

finally:
    driver.quit()

# Convertir los datos en un DataFrame
df = pd.DataFrame(products)
df.to_csv("bicicletas_niños_products_ebay.csv", index=False)
print("Scraping completado. Datos guardados en 'bicicletas_niños_products_ebay.csv'.")


#EDA
# Tratamiento de datos
import pandas as pd
# Ignorar warnings
import warnings
warnings.filterwarnings("ignore")
# Configuración
pd.set_option('display.max_columns', None)# para poder visualizar todas las columnas de los DataFrames
pd.set_option('display.max_rows', None)# para poder visualizar todas las filas de los DataFrames
pd.set_option('display.max_colwidth', None) #para ampliar el tamaño de las columnas
#importar la biblioteca de numpy:
import numpy as np
import os
import sys #permite navegar por el sistema
sys.path.append("../") #solo aplica al soporte
import re
#import src.soporte_EDA as se

# Visualización

import matplotlib.pyplot as plt
import seaborn as sns

pd.options.display.float_format = '{:.2f}'.format # para redondearlo todo a 2 decimalesort matplotlib.pyplot as plt

df_bicicletas = pd.read_csv(f"bicicletas_niños_products_ebay.csv")

# 1. Limpieza

df_bicicletas_filtrado = df_bicicletas.dropna(subset=['Title']).reset_index() #eliminar las filas que está vacías

#dividir la subcategoría en dos columnas diferentes:state y seller_type
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado.Sub_title.str.split('|',expand=True)[0]
df_bicicletas_filtrado['Seller_type'] = df_bicicletas_filtrado.Sub_title.str.split('|',expand=True)[1]

## a). Tratamiento de las columnas numéricas para convertirlas en números

#Tratamiento columna Shipping_cost
df_bicicletas_filtrado['Shipping_cost'] = df_bicicletas_filtrado['Shipping_cost'].str.replace(' EUR de envío', '') #sustituyo " EUR de envio" por nada
df_bicicletas_filtrado['Shipping_cost'] = df_bicicletas_filtrado['Shipping_cost'].str.replace('+', '') #sustituyo "+" por nada
df_bicicletas_filtrado['Shipping_cost'] = df_bicicletas_filtrado['Shipping_cost'].str.replace(',', '.') #sustituyo "," por '.'
df_bicicletas_filtrado['Shipping_cost'] = df_bicicletas_filtrado['Shipping_cost'].str.strip() #elimino espacios vacios al principio y al final
df_bicicletas_filtrado['Shipping_cost'] = df_bicicletas_filtrado['Shipping_cost'].str.replace('Envío gratis', '0.00') #sustituyo "Envío gratis" por '.'

def conversion_float(texto):
    """
    Convierte un valor dado a tipo flotante.

    Parámetros:
    texto (str): El texto o valor que se desea convertir a un número flotante.

    Retorna:
    float: El valor convertido a flotante si es posible.
    numpy.nan: Si ocurre un error en la conversión (por ejemplo, entrada no válida).

    Notas:
    Requiere que numpy esté importado como np para utilizar np.nan.
    """
    try:
        return float(texto)
    except:
        return np.nan

df_bicicletas_filtrado["Shipping_cost"] = df_bicicletas_filtrado["Shipping_cost"].apply(conversion_float) #la convierto en tipo float


#Tratamiento columna Price:
df_bicicletas_filtrado['Price'] = df_bicicletas_filtrado['Price'].str.replace(' EUR', '') #sustituyo " EUR" por nada
df_bicicletas_filtrado['Price'] = df_bicicletas_filtrado['Price'].str.replace(',', '.') #sustituyo "," por '.'
df_bicicletas_filtrado['Price'] = df_bicicletas_filtrado['Price'].str.strip() #elimino espacios vacios al principio y al final

df_bicicletas_filtrado['Starting_price'] = df_bicicletas_filtrado.Price.str.split(' a ',expand=True)[0]
df_bicicletas_filtrado['Ending_price'] = df_bicicletas_filtrado.Price.str.split(' a ',expand=True)[1]

df_bicicletas_filtrado["Price"] = df_bicicletas_filtrado["Price"].apply(conversion_float) #la convierto en tipo float

lista_indices_precios_vacios_sup_1000 = df_bicicletas_filtrado[df_bicicletas_filtrado.Price.isnull()][df_bicicletas_filtrado.Ending_price.isnull()].index #para sacar el índice de los que se han quedado nulos y que son mayores a 1000
for indice in lista_indices_precios_vacios_sup_1000: #correción de los valores superiores a 1000
    df_bicicletas_filtrado.Price[indice]  = float(df_bicicletas_filtrado.Starting_price[indice][0]+df_bicicletas_filtrado.Starting_price[indice][2:8])

lista_indices_precios_vacios_rango = df_bicicletas_filtrado[df_bicicletas_filtrado.Price.isnull()].index # para sacar los productos vacios porque tienen un rango de precios
for indice in lista_indices_precios_vacios_rango: #correccion de estos valores
    try:
        df_bicicletas_filtrado.Price[indice]  = (float(df_bicicletas_filtrado.Starting_price[indice])+float(df_bicicletas_filtrado.Ending_price[indice]))/2
    except:
        np.nan

lista_indices_starting_price_o_ending_price_sup_1000= df_bicicletas_filtrado[df_bicicletas_filtrado.Price.isnull()].index #para sacar los productos que tenian un rango de precios y que se han quedado vacios por ser superiores a 1000
for indice in lista_indices_starting_price_o_ending_price_sup_1000: #corrección de estos valores
    if len(df_bicicletas_filtrado.Starting_price[indice])==8:
        df_bicicletas_filtrado.Starting_price[indice]  = float(df_bicicletas_filtrado.Starting_price[indice][0]+df_bicicletas_filtrado.Starting_price[indice][2:8])
    else:
        df_bicicletas_filtrado.Starting_price[indice] = float(df_bicicletas_filtrado.Starting_price[indice])
    if len(df_bicicletas_filtrado.Ending_price[indice])==8:
        df_bicicletas_filtrado.Ending_price[indice]  = float(df_bicicletas_filtrado.Ending_price[indice][0]+df_bicicletas_filtrado.Ending_price[indice][2:8])
    else:
        df_bicicletas_filtrado.Ending_price[indice] = float(df_bicicletas_filtrado.Ending_price[indice])

    df_bicicletas_filtrado.Price[indice]  = ((df_bicicletas_filtrado.Starting_price[indice])+(df_bicicletas_filtrado.Ending_price[indice]))/2


#creación de la columna TOTAL_COST
df_bicicletas_filtrado["Total_cost"] = None
for indice in df_bicicletas_filtrado.index:
    if pd.isna(df_bicicletas_filtrado.Shipping_cost[indice]): #si el valor del campo Shipping_Cost es nulo
        df_bicicletas_filtrado["Total_cost"][indice] = df_bicicletas_filtrado["Price"][indice]
    else:
        df_bicicletas_filtrado["Total_cost"][indice] = df_bicicletas_filtrado["Price"][indice]+df_bicicletas_filtrado["Shipping_cost"][indice]

## b). Tratamiento de la columna State
#códigos para limpiar la categoría y dejarla solo en 4: Nuevo, Usado,  Solo piezas, Sin información
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].str.strip()
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('Nuevo (de otro tipo)', 'Totalmente nuevo')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('**EL ARTÍCULO ESTÁ COMO NUEVO**', 'Usado')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('**EL ARTÍCULO HA SIDO LIGERAMENTE USADO**', 'Usado')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('**ARTÍCULO ESTÁ COMO NUEVO**', 'Usado')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('EXCELENTE ESTADO CASI COMO NUEVO ¡POCO USADO!!!', 'Usado')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('ENTREGA GRATUITA 1-3 DÍAS CON DEVOLUCIONES SIN COMPLICACIONES, ¡30 DÍAS!', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('¡ENVÍO GRATUITO DE 1-3 DÍAS CON DEVOLUCIONES SIN PROBLEMAS DE 30 DÍAS!', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('Devolución gratuita y reembolso completo si no te gusta', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('★gran bicicleta infantil★con muelle★para niños talla 120-135 cm★', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('★gran bicicleta para niños★horquilla de resorte★para niños talla 120-135 cm★', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('15% de descuento código SAVVY15 gasto mínimo 9,99 descuento máximo 75', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('gran oferta', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('OPTIMUS✔️️Plegable✔️Alcance 70-80 km✔️Puerto USB✔️', None)
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('**EL ARTÍCULO DEBE USARSE SOLO PARA PIEZAS**', 'Solo piezas')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].fillna('Sin información')
df_bicicletas_filtrado['State'] = df_bicicletas_filtrado['State'].replace('Totalmente nuevo', 'Nuevo')

## b). Tratamiento de la columna Title
#Para extraer las pulgadas de la bicicleta:
df_bicicletas_filtrado["Pulgadas"] = df_bicicletas_filtrado['Title'].str.extract(r'(\d+)\s*pulgadas',re.IGNORECASE, expand = True)
df_bicicletas_filtrado["Pulgadas1"] = df_bicicletas_filtrado['Title'].str.extract(r'(\d+)\s*"',re.IGNORECASE, expand = True)

lista_pulgadas_nulas_con_pulgadas1_con_info = df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas1.notna()][df_bicicletas_filtrado.Pulgadas.isnull()].index
for indice in lista_pulgadas_nulas_con_pulgadas1_con_info:
    df_bicicletas_filtrado.Pulgadas[indice]= df_bicicletas_filtrado.Pulgadas1[indice]

lista_pulgadas_validas = ['12', '14', '16', '18', '20', '24', '26'] #para dejar solo las pulgadas correctas
def pulgadas_validas(pulgada):
    """
    Verifica si una medida en pulgadas es válida según una lista predefinida.

    Parámetros:
    pulgada (float o int): El valor en pulgadas que se desea validar.

    Retorna:
    float o int: El valor de entrada si se encuentra en la lista de pulgadas válidas.
    numpy.nan: Si el valor no está en la lista predefinida de pulgadas válidas.

    Notas:
    - La lista `lista_pulgadas_validas` debe estar definida en el entorno donde se use esta función.
    - Requiere que numpy esté importado como np para utilizar np.nan.
    """
    if pulgada in lista_pulgadas_validas:
        return pulgada
    else:
        np.nan

df_bicicletas_filtrado['Pulgadas'] = df_bicicletas_filtrado['Pulgadas'].apply(pulgadas_validas) #aplicar la función

df_bicicletas_filtrado['Pulgadas'] = df_bicicletas_filtrado['Pulgadas'].fillna('Sin información') #sustituir los nulos por sin información

##c). Eliminar las columnas que no voy a usar:
del df_bicicletas_filtrado['Pulgadas1']
del df_bicicletas_filtrado['Sales']
del df_bicicletas_filtrado['Sub_title']

## d). Incluir informació adicional según las pulgadas de la bicicleta:
df_bicicletas_filtrado["Estatura_niño_cm"] = np.nan
df_bicicletas_filtrado["Entrepierna_cm"] = np.nan
df_bicicletas_filtrado["Rango_edad_años"] = np.nan
for indice in df_bicicletas_filtrado.index:
    if df_bicicletas_filtrado['Pulgadas'][indice] == '12':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '85 cm a 103 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '30 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '1,5 - 3'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '14':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '103 cm a 107 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '33 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '3-4'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '16':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '107 cm a 119 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '36 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '4-6'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '18':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '119 cm a 125 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '41 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '5-7'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '20':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '125 cm a 130 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '51 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '6-8'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '24':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '130 cm a 140 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '61 cm'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '8-12'
    elif df_bicicletas_filtrado['Pulgadas'][indice] == '26':
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = '140 cm a 160 cm'
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = '66 cm ó +'
        df_bicicletas_filtrado["Rango_edad_años"][indice] = '12 ó +'
    else:
        df_bicicletas_filtrado["Estatura_niño_cm"][indice] = None
        df_bicicletas_filtrado["Entrepierna_cm"][indice] = None
        df_bicicletas_filtrado["Rango_edad_años"][indice] = None 

#GUARDAR EL DF LIMPIO
df_bicicletas_filtrado.to_pickle("bicicletas_niños_products_ebay_clean.pkl")

# 2. Muestra de una tabla con los tipos de bicicletas que hay y para que edades, y estaturas están recomendadas: 
print(f'Los tipos de bicicletas que existen de niños son:')
df_detalle_tipo_bicicletas_niños= df_bicicletas_filtrado.groupby("Pulgadas")[['Estatura_niño_cm','Entrepierna_cm','Rango_edad_años']].value_counts().reset_index()
del df_detalle_tipo_bicicletas_niños['count']
print(df_detalle_tipo_bicicletas_niños)


# 3. Visualizaciones 
#Creación DF agrupados:
df_bicicletas_filtrado.groupby('Pulgadas')[['Price', 'Shipping_cost', 'Total_cost']].mean()
df_bicicletas_filtrado.groupby('Location')[['Price', 'Shipping_cost', 'Total_cost']].mean()
df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == '16'].groupby('Location')[['Price', 'Shipping_cost', 'Total_cost']].mean()
df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == '12'].groupby('State')[['Price', 'Shipping_cost', 'Total_cost']].mean()

#Incorporación columna %
count_state = df_bicicletas_filtrado.State.value_counts().reset_index()
count_state['%_state'] = count_state['count']/count_state['count'].sum()*100
count_pulgadas = df_bicicletas_filtrado.Pulgadas.value_counts().reset_index()
count_pulgadas['%_pulgadas'] = count_pulgadas['count']/count_pulgadas['count'].sum()*100
count_location = df_bicicletas_filtrado.Location.value_counts().reset_index()
count_location['%_location'] = count_location['count']/count_location['count'].sum()*100
count_location

#creación del orden de las columnas para los gráficos
orden_columnas_pais=count_location.Location
orden_columnas_state_general = count_state.State
orden_columnas_pulgadas_general = count_pulgadas.Pulgadas
orden_Seller_type = df_bicicletas_filtrado.Seller_type.value_counts().index

#Creación de la primera visualización
fig, axes = plt.subplots(1, 3, sharex= False, sharey=True, figsize= (20,7))
fig.suptitle('Porcentaje de productos totales encontrados en Ebay', fontsize=18)

sns.barplot(data=count_state, x='State', y='%_state', palette='cubehelix', ax=axes[0], order=orden_columnas_state_general)
axes[0].set_ylabel('%', fontsize = 12)
axes[0].set_xlabel('State', fontsize = 12)
axes[0].set_title('% Artículos según estado bicicleta', fontsize = 14)
axes[0].spines['right'].set_visible(False)
axes[0].spines['top'].set_visible(False)
axes[0].legend()

sns.barplot(data=count_pulgadas, x='Pulgadas', y='%_pulgadas', palette='cubehelix', ax=axes[1], order= orden_columnas_pulgadas_general)
axes[1].set_ylabel('%', fontsize = 12)
axes[1].set_xlabel('Pulgadas', fontsize = 12)
axes[1].set_title('% Artículos según pulgadas bicicleta', fontsize = 14)
axes[1].spines['right'].set_visible(False)
axes[1].spines['top'].set_visible(False)
axes[1].legend()

sns.barplot(data=count_location.head(10), x='Location', y='%_location', palette='cubehelix', ax=axes[2], order = orden_columnas_pais)
axes[2].set_ylabel('%', fontsize = 12)
plt.xticks(rotation=90, fontsize=10)
axes[2].set_xlabel('Location', fontsize = 12)
axes[2].set_title('% Artículos según desde donde se realiza el envío', fontsize = 14)
axes[2].spines['right'].set_visible(False)
axes[2].spines['top'].set_visible(False)
axes[2].legend();

#Creación de la segunda visualización:
fig, axes = plt.subplots(1, 3, sharex= False, sharey=True, figsize= (20,7))
fig.suptitle('Promedio del coste total de todos los productos encontrados en EBAY', fontsize=18)

sns.barplot(data=df_bicicletas_filtrado.groupby(['State','Seller_type'])[['Price', 'Shipping_cost', 'Total_cost']].mean(), x='State', y='Total_cost', hue='Seller_type', palette='cubehelix', ax=axes[0], order=orden_columnas_state_general, hue_order=orden_Seller_type)
axes[0].set_ylabel('Coste', fontsize = 12)
axes[0].set_xlabel('State', fontsize = 12)
axes[0].set_title('Coste medio según estado bicicleta', fontsize = 14)
axes[0].spines['right'].set_visible(False)
axes[0].spines['top'].set_visible(False)
axes[0].legend().remove()

sns.barplot(data=df_bicicletas_filtrado.groupby(['Pulgadas','Seller_type'])[['Price', 'Shipping_cost', 'Total_cost']].mean(), x='Pulgadas', y='Total_cost', hue='Seller_type', palette='cubehelix', ax=axes[1], order=orden_columnas_pulgadas_general, hue_order=orden_Seller_type)
axes[1].set_ylabel('Coste', fontsize = 12)
axes[1].set_xlabel('Pulgadas', fontsize = 12)
axes[1].set_title('Coste medio según pulgadas', fontsize = 14)
axes[1].spines['right'].set_visible(False)
axes[1].spines['top'].set_visible(False)
axes[1].legend().remove();


sns.barplot(data=df_bicicletas_filtrado.groupby(['Location','Seller_type'])[['Price', 'Shipping_cost', 'Total_cost']].mean(), x='Location', y='Total_cost', hue='Seller_type', palette='cubehelix', ax=axes[2], order=orden_columnas_pais, hue_order=orden_Seller_type)
axes[2].set_ylabel('Coste', fontsize = 12)
plt.xticks(rotation=90, fontsize=10)
axes[2].set_xlabel('Location', fontsize = 12)
axes[2].set_title('Coste medio desde donde se realiza el envío', fontsize = 14)
axes[2].spines['right'].set_visible(False)
axes[2].spines['top'].set_visible(False)
axes[2].legend(bbox_to_anchor = (1.05,1));

plt.show()

#4. Función para mostrar solo las bicicletas que le interese según la estatura del niño:
def propuesta_bicicleta_niño ():
    """
    Recomienda el tamaño adecuado de bicicleta para un niño en función de su estatura.

    Solicita al usuario que introduzca la altura del niño en centímetros y determina el tamaño
    de la bicicleta (en pulgadas) más adecuado según los rangos establecidos.

    Parámetros:
    No tiene parámetros de entrada.

    Retorna:
    str o None: 
        - El tamaño de la bicicleta en pulgadas si la estatura del niño está dentro de los rangos definidos.
        - None si el niño no puede usar bicicletas infantiles o necesita una bicicleta de adulto.

    Notas:
    - Los rangos de altura están definidos de la siguiente manera:
        < 85 cm: No puede usar bicicletas infantiles.
        85-103 cm: 12 pulgadas.
        103-107 cm: 14 pulgadas.
        107-119 cm: 16 pulgadas.
        119-125 cm: 18 pulgadas.
        125-130 cm: 20 pulgadas.
        130-140 cm: 24 pulgadas.
        140-160 cm: 26 pulgadas.
        > 160 cm: Necesita una bicicleta de adultos.
    - La función utiliza `input` para obtener la estatura del niño, lo que requiere interacción del usuario.
    """
    Estatura_niño =float(input(f'Por favor, introduzca la altura del niñ@ en centímetros'))
    if Estatura_niño <85:
        print(f'Según los datos aportados, todavía no puede coger bicicletas de niños')
        pulgadas = None
    if Estatura_niño >=85 and Estatura_niño<103:
        pulgadas = '12'
    if Estatura_niño >=103 and Estatura_niño<107:
        pulgadas = '14'    
    if Estatura_niño >=107 and Estatura_niño<119:
        pulgadas = '16'
    if Estatura_niño >=119 and Estatura_niño<125:
        pulgadas = '18'        
    if Estatura_niño >=125 and Estatura_niño<130:
        pulgadas = '20'      
    if Estatura_niño >=130 and Estatura_niño<140:
        pulgadas = '24'   
    if Estatura_niño >=140 and Estatura_niño<=160:
        pulgadas = '26'
    if Estatura_niño >160:
        print(f'Según los datos aportados, necesitaría una bicicleta de adultos')
        pulgadas = None
    return pulgadas  


pulgadas = propuesta_bicicleta_niño() 

#para informarle del tipo de pulgada que necesita:
if pulgadas == None:
    print(f'Esta búsqueda no le puede facilitar opciones')
else:
    print(f'Según los datos aportados, necesitaría una bicicleta de {pulgadas} pulgadas')

#representación visual de la información para ese tipo de bicicleta:
if pulgadas == None:
    print(f'')
else:
    count_state = df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas].State.value_counts().reset_index()
    count_state['%_state'] = count_state['count']/count_state['count'].sum()*100
    count_location = df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas].Location.value_counts().reset_index()
    count_location['%_location'] = count_location['count']/count_location['count'].sum()*100

     
    orden_columnas= count_location.Location  
    orden_columnas_state = count_state.State 
    orden_Seller_type = df_bicicletas_filtrado.Seller_type.value_counts().index
    fig, axes = plt.subplots(1, 2, sharex= False, sharey=True, figsize= (20,7))
    fig.suptitle(f'Porcentaje de productos para {pulgadas} pulgadas', fontsize=18)
    sns.barplot(data=count_state, x='State', y='%_state', palette='cubehelix', ax=axes[0], order=orden_columnas_state)
    axes[0].set_ylabel('%', fontsize = 12)
    axes[0].set_xlabel('State', fontsize = 12)
    axes[0].set_title('% Artículos según estado bicicleta', fontsize = 14)
    axes[0].spines['right'].set_visible(False)
    axes[0].spines['top'].set_visible(False)
    axes[0].legend()

    sns.barplot(data=count_location, x='Location', y='%_location', palette='cubehelix', ax=axes[1], order=orden_columnas)
    axes[1].set_ylabel('%', fontsize = 12)
    plt.xticks(rotation=90, fontsize=10)
    axes[1].set_xlabel('Location', fontsize = 12)
    axes[1].set_title('% Artículos según desde donde se realiza el envío', fontsize = 14)
    axes[1].spines['right'].set_visible(False)
    axes[1].spines['top'].set_visible(False)
    axes[1].legend();

        
    fig, axes = plt.subplots(1, 2, sharex= False, sharey=True, figsize= (20,7))
    fig.suptitle(f'Promedio del coste total de los productos para {pulgadas} pulgadas', fontsize=18)
    sns.barplot(data=df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas].groupby(['State','Seller_type'])[['Price', 'Shipping_cost', 'Total_cost']].mean(), x='State', y='Total_cost', hue='Seller_type', palette='cubehelix', ax=axes[0], order=orden_columnas_state, hue_order=orden_Seller_type)
    axes[0].set_ylabel('Coste', fontsize = 12)
    axes[0].set_xlabel('State', fontsize = 12)
    axes[0].set_title('Coste medio según estado bicicleta', fontsize = 14)
    axes[0].spines['right'].set_visible(False)
    axes[0].spines['top'].set_visible(False)
    axes[0].legend().remove

    sns.barplot(data=df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas].groupby(['Location','Seller_type'])[['Price', 'Shipping_cost', 'Total_cost']].mean(), x='Location', y='Total_cost', hue='Seller_type', palette='cubehelix', ax=axes[1], order=orden_columnas, hue_order=orden_Seller_type)
    axes[1].set_ylabel('Coste', fontsize = 12)
    plt.xticks(rotation=90, fontsize=10)
    axes[1].set_xlabel('Location', fontsize = 12)
    axes[1].set_title('Coste medio desde donde se realiza el envío', fontsize = 14)
    axes[1].spines['right'].set_visible(False)
    axes[1].spines['top'].set_visible(False)
    axes[1].legend();

#Detalle de los productos disponibles en ebay:
if pulgadas == None:
    print(f'')
else:
    print(f'El detalle de los productos disponibles en Ebay para esta categoría son:')
    print(df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas][['Title', 'Total_cost', 'State','Seller_type', 'Location']])

#link a cada uno de los productos
if pulgadas == None:
    print(f'')
else:
    print(f'El enlace a cada una de ellas es:')
    print(df_bicicletas_filtrado[df_bicicletas_filtrado.Pulgadas == pulgadas]['link'])

#Cierre del código
plt.show()
print(f'El código ha finalizado, espero que le haya sido de ayuda')