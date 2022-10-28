#### <div class="alert alert-info"> Мой вариант работы. Чтобы сделать работу побыстрее не буду тратить время на оформление и далее по тексту буду писать в комментариях, к тому же так чуть компактнее </b> </div>

# Надеюсь ничего не наврал при копировании, тем более после копирования в .py вносил 
# правки в ноутбук и потом опять сюда

import pandas as pd
from IPython.display import display
from google.colab import drive
from IPython.display import display
import seaborn as sns

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#### <div class="alert alert-info"> Несколько команд для варианта выполнения в коллабе. Архив с данными должен быть на гугл диске</b> </div>

drive.mount('/content/gdrive/')

!ls /content/gdrive/

!ls -l /content/gdrive/MyDrive/ads_leads_purchases.zip

!unzip -q /content/gdrive/MyDrive/ads_leads_purchases.zip

!ls -1
# Почти закончил разбираться с библиотекой gspread чтобы руками не копировать туда данные
# но почему-то не скачивался client secrets JSON keyfile, за неимением времени пришлось бросить эту затею 


ads = pd.read_csv('ads.csv')
leads = pd.read_csv('leads.csv')
purchases = pd.read_csv('purchases.csv')

display(ads.head())
display(leads.head())
display(purchases.head())

# пример подключения к базе

database="test_de",
user="jovyan",
password="jovyan",
host="localhost",
port=15432

ads_base = pd.read_sql(
    """SELECT * 
        FROM "leads"
        """,
    con="postgresql://jovyan:jovyan@localhost:15432/test_de"
)

ads_base.head()


# В таблице ads нет пропусков по основным полям, можно сделать первую часть 
# итоговой сводной таблицы - посчитать "Количество кликов", "Расходы на рекламу". 
# Группировать буду по месяцу
ads.info()
print('_______________________________________________')
leads.info()
print('_______________________________________________')
purchases.info()


# по ads по совокупности основных полей дубликатов не нашел
ads.drop_duplicates(['created_at', 'd_utm_source', 'd_utm_medium', 
             'd_utm_campaign', 'd_utm_content']).shape
             
             
# по leads так же
print(leads.lead_id.nunique())
leads.drop_duplicates(['lead_created_at', 'lead_id', 'd_lead_utm_source', 
                       'd_lead_utm_medium', 'd_lead_utm_campaign',
                       'd_lead_utm_content']).shape
                       
# по purchases так же
print(purchases.purchase_id.nunique())
purchases.drop_duplicates(['purchase_id', 'client_id']).shape

# Дату указываю в формате год+месяц, в рассматриваемом случае это не критично, 
# но если период был бы два года, то месяцы бы повторялись в годах и статистика 
# была бы некорректная
ads['ad_year_month'] = ads['created_at'].apply(lambda x: x[:7])
ads['ad_year_month'].head(3)

leads['lead_year_month'] = leads['lead_created_at'].apply(lambda x: x[:7])
leads['lead_year_month'].head(3)

purchases['pur_year_month'] = purchases['purchase_created_at'].apply(lambda x: x[:7])
purchases['pur_year_month'].head(3)
                       
ads['created_at'] = pd.to_datetime(ads['created_at'])
leads['lead_created_at'] = pd.to_datetime(leads['lead_created_at'])
purchases['purchase_created_at'] = pd.to_datetime(purchases['purchase_created_at'])

display(ads.describe(datetime_is_numeric=True))
display(leads.describe(datetime_is_numeric=True))
purchases.describe(datetime_is_numeric=True)

# По всей вероятности в данных есть выбросы, но я не буду ничего удалять
# тема исследования выбросов требует отдельного углубенного анализа, 
# обсуждения с бизнесом, исследования пайплана сбора 
# и обработки данных и т.д. На первый взгляд может показаться, что 
# сумма около 250000 для салона красоты явно выброс, с другой стороны
# возможно есть какие-то абонементы на массаж + дополнительные люксовые услуги
# на год либо даже больше (либо на 100 сеансов), которые можно купить одним чеком. 
# Как, например, с фитнесом - в одном и том же клубе может быть 
# абонемент за 20 тысяч и за 170 тысяч на одинаковый период. 
# Ввиду изложенного и отсутствия возможности провести более детальный 
# анализ в контексте выбросов, оставлю данные "как есть"

sns.boxplot(purchases.m_purchase_amount)

sns.boxplot(ads.m_cost)

sns.boxplot(ads.m_clicks)

# За базис взял компании из таблицы ads. leads с таблицей ads не матчатся 1 к 1, 
# ввиду пропусков в leads. Как мне кажется в текущих данных важнее исходить 
# из тех кампаний, по которым мы можем однозначно аллоцировать расходы

click_cost = ads.groupby(['ad_year_month', 'd_utm_source', 'd_utm_medium', 
             'd_utm_campaign'], as_index=False).agg({'m_clicks':'sum', 'm_cost':'sum'}) \
              .rename(columns={'m_clicks': 'Количество кликов', 'm_cost': 'Расходы на рекламу'})

click_cost.head(10)

# Кажется это самые малоинформативные строки в leads - с шестью пропущенными 
# значениям из 8 возможных, я удалю их
leads[leads['d_lead_utm_source'].isna() & leads['d_lead_utm_campaign'].isna()
      & leads['d_lead_utm_medium'].isna() & leads['d_lead_utm_content'].isna() 
      & leads['d_lead_utm_term'].isna() & leads['client_id'].isna()].shape[0]

# Можно было воспользоваться dropna
# leads = leads.dropna(how='all', 
#                       subset=['d_lead_utm_source', 'd_lead_utm_campaign', 
#                              'd_lead_utm_medium', 'd_lead_utm_content', 
#                              'd_lead_utm_term', 'client_id'])
# но дропы (drop, dropna) работают чуть медленнее, чем если использовать переприсвоение.
# На маленьких данных и при разовом использовании почти незаметно,
# но на больших таблицах с большим количеством повторений это уже 
# становится более явно, поэтому я предпочитаю не использовать дропы

leads = leads[~(leads['d_lead_utm_source'].isna() & leads['d_lead_utm_campaign'].isna()
      & leads['d_lead_utm_medium'].isna() & leads['d_lead_utm_content'].isna() 
      & leads['d_lead_utm_term'].isna() & leads['client_id'].isna())]

print(leads.shape)
leads.head()

# Выберем строки где хотя бы одно значение из столбцов 
# d_lead_utm_source, d_lead_utm_campaign, d_lead_utm_medium
# пропущено, получается достаточно много - больше половины датафрейма
# посмотрим на уникальные d_lead_utm_source. Примечательно, что здесь 
# сравнительно много источников трафика, учитывая тот факт, что
# когда мы строили свод с количеством кликов и расходов на рекламу, там был источник только yandex

leads_sh = leads[leads['d_lead_utm_source'].isna() | leads['d_lead_utm_campaign'].isna()
                      | leads['d_lead_utm_medium'].isna()]

print(leads_sh.shape[0])
leads_sh['d_lead_utm_source'].unique()

# также отдельно интересно отметить, что запись с источником yandex
# в полученном в предыдущей ячейке датафрейме встречается только 
# один раз, при этом остальные важные поля такие, например, как 
# тип трафика (d_lead_utm_medium) и кампания (d_lead_utm_campaign) в ней пропущены

leads_sh[leads_sh['d_lead_utm_source'] == 'yandex']

# С учетом всего вышеизложенного можно сделать вывод, что по источникам 
# трафика кроме yandex на имеющихся данных нормальную сквозную аналитику 
# построить не удастся, т.к. по ним нет расходов.
# К сожалению пришлось удалить огромную часть данных, но как я уже сказал, 
# по моему мнению на тех данных, которы мы удалили нельзя было построить 
# нормальную аналитику garbage_in = garbage_out 
# Еще удалим одну строчку из предыдущей ячейки и две пустые строки по 
# полю d_lead_utm_content, они уже погоды не сделают,
# но данные будут почище и не будет проблем с джойном
print(list(leads['d_lead_utm_source'].unique()))

leads_cl = leads[leads['d_lead_utm_source'].isin(['yandex'])]
# leads_cl = leads_cl.dropna(how='any', 
#                            subset=['d_lead_utm_source', 'd_lead_utm_campaign', 
#                            'd_lead_utm_medium', 'd_lead_utm_content'])
leads_cl = leads_cl[~(leads_cl['d_lead_utm_source'].isna() | leads_cl['d_lead_utm_campaign'].isna()
                      | leads_cl['d_lead_utm_medium'].isna() | leads_cl['d_lead_utm_content'].isna())]


print(leads_cl.shape)
leads_cl.head()

# Также уберем строки в leads с отсутствующим client_id,
# иначе не построить связь с продажами
leads_cl = leads_cl[~leads_cl['client_id'].isna()]
print(leads_cl.shape)
leads_cl.head()

ads['d_utm_campaign'] = ads['d_utm_campaign'].astype('str')
ads['d_utm_medium'] = ads['d_utm_medium'].astype('str')
ads['d_utm_content'] = ads['d_utm_content'].astype('str')


#Не смотря на указание в задании по ключевым словам не джойнил, т.к. поле преимущественно пустое.

ads_leads = ads.merge(leads_cl, how='inner', 
                      left_on=['created_at', 'd_utm_source', 'd_utm_medium', 
                               'd_utm_campaign', 'd_utm_content'],
                      right_on=['lead_created_at', 'd_lead_utm_source',  
                               'd_lead_utm_medium', 'd_lead_utm_campaign',
                               'd_lead_utm_content'])
print(ads_leads.shape)
ads_leads.head()

n_leads = ads_leads.groupby(['ad_year_month', 'd_utm_source', 'd_utm_medium', 
             'd_utm_campaign'], as_index=False).agg({'lead_id':'nunique'}) \
              .rename(columns={'lead_id': 'Количество лидов'})
              
n_leads.head(10)

df_all = ads_leads.merge(purchases, how='inner', on='client_id')

print(df_all.shape)
df_all.head()

df_all['dlt_lead_pur'] = (df_all['purchase_created_at'] - df_all['lead_created_at']).dt.days
df_all['dlt_lead_pur']      
      
df_all[df_all['dlt_lead_pur'].isna()]

min_delta = df_all.groupby('purchase_id', as_index=False) \
                        .agg({'dlt_lead_pur':'min'}) \
                        .rename(columns={'dlt_lead_pur': 'min_delta'})
min_delta

min_delta[min_delta['min_delta'].isna()]

df_all_v2 = df_all.merge(min_delta, how='inner', on='purchase_id')
print(df_all_v2.shape)
df_all_v2.head()


# Атрибуция лид - покупка. Отбираем значения по трем правила:
# 1) временная дельта от лида до покупки не отрицательна, т.к. мы вычитал дату покупки
# из даты лида и нам нужно, чтобы дата покупки была больше
# 2) дельта от лида до покупки равна минимальной дельте покупки, т.к.
# мы хотим атрибутировать только ближайший лид
# 3) дельта от лида до покупки должна быть не более 15 дней, я взял 15 включительно

df_fin = df_all_v2[(df_all_v2['dlt_lead_pur'] >= 0) & (df_all_v2['dlt_lead_pur'] == df_all_v2['min_delta'])
                  & (df_all_v2['dlt_lead_pur'] <= 15)]

print(df_fin.shape)
df_fin.head()

# дубликаты по паре атрибутов client_id, purchase_id
df_fin[df_fin.duplicated(['client_id', 'lead_id'], keep=False)].head()

# Отдельно удалим дубликаты по паре атрибутов client_id, purchase_id,
# чтобы не смотря на наши предыдущие условия на один лид не атрибутировались
# несколько покупок одного клиента, пусть они и в течении 15 дней от лида

df_fin = df_fin.drop_duplicates(['client_id', 'lead_id'])
print(df_fin.shape)
df_fin.head()

# Есть дубликаты по полям ['client_id', 'purchase_id']
df_fin[df_fin.duplicated(['client_id', 'purchase_id'], keep=False)]     

# Также удалим иные данные, которые содержат какую-либо нелогичность -
# дубликаты по полям ['client_id', 'purchase_id'], продажи с нулем 
# по полю m_purchase_amount

df_fin = df_fin.drop_duplicates(['client_id', 'purchase_id'])
df_fin = df_fin[df_fin['m_purchase_amount'] != 0]

print(df_fin.shape)
df_fin.head()

n_sales_rev = df_fin.groupby(['ad_year_month', 'd_utm_source', 'd_utm_medium', 'd_utm_campaign'], 
               as_index=False).agg({'purchase_id':'nunique', 'm_purchase_amount':'sum'}) \
              .rename(columns={'purchase_id': 'Количество продаж', 'm_purchase_amount': 'Выручка'})

n_sales_rev.head(15)

click_cost['d_utm_campaign'] = click_cost['d_utm_campaign'].astype('str')
n_leads['d_utm_campaign'] = n_leads['d_utm_campaign']
n_sales_rev['d_utm_campaign'] = n_sales_rev['d_utm_campaign'].astype('str')

# Либо можно сделать везде inner, но тогда в финальную таблицу получается 
# не будут попадать все косты и мы можем упустить, что были потрачены 
# деньги на лиды, которые не дали продаж либо на рекламу, которая не дала лидов, 
# что на мой взгляд не совсем правильно.
# Отмечу, что в итоговую таблицу попадают не все доходы, так, например,
# одна из продаж не имеет client_id. Также мы убирали повторные покупки
# клиента после лида, однако, если считать, что сейчас не изучаем
# финансовые показатели в целом, а смотрим именно рентабельность
# рекламных кампаний, то считаю, что это допустимо
# Не забудем убрать строки, где расходы на рекламу равны нулю

df_fin_gr = click_cost.merge(n_leads, how='left', 
                         on=['ad_year_month', 'd_utm_source', 'd_utm_medium', 'd_utm_campaign']) \
                      .merge(n_sales_rev, how='left', 
                         on=['ad_year_month', 'd_utm_source', 'd_utm_medium', 'd_utm_campaign']) 

df_fin_gr = df_fin_gr[df_fin_gr['Расходы на рекламу'] != 0]
df_fin_gr.head(10)

df_fin_gr['CPL'] = (df_fin_gr['Расходы на рекламу'] / df_fin_gr['Количество лидов']).round(2)
df_fin_gr['ROAS'] = (df_fin_gr['Выручка'] / df_fin_gr['Расходы на рекламу']).round(2)

df_fin_gr

df_fin_gr.to_excel('df_fin_gr.xlsx', index=False)