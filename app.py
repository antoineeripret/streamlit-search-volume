#libraries used in the script
from io import StringIO
from urllib import request
import streamlit as st
import pandas as pd
import requests
import json 
from io import StringIO

def convert_df(df):
    return df.to_csv().encode('utf-8')

st.title('Download Search Volume')

st.markdown(
'''Search volume application done by [Antoine Eripret](https://twitter.com/antoineripret). You can report a bug or an issue in [Github](https://github.com/antoineeripret/streamlit-search-volume).

You can get search volume from [Keyword Surfer](https://surferseo.com/keyword-surfer-extension/) or [Semrush API](https://www.semrush.com/api-analytics/). For the later, **an API is required and you will spend 10 credits per keyword**. 

Note that even though there is no hard limit, **I don't advise to retrieve more than 10.000 keywords at once using this tool**. The application is very likely to crash.


''')

with st.expander('STEP 1: Configure your extraction'):
    st.markdown('Use two letters ISO code (es,fr,de...). **Please check Keyword Surfer\'s or Semrush\'s documentation to check if your country is available.** Not all of them are.')
    source = st.selectbox('Source', ('Keyword Surfer (FREE)', 'Semrush (Paid)'))
    country = st.text_input('Country')

    st.write('If a keyword is not included in a database, volume returned will be 0. **Which doesn\'t mean that it has no search volume ;)**')
    uploaded_file = st.file_uploader("Upload your keywords")

    if uploaded_file is not None:
        # Can be used wherever a "file-like" object is accepted:
        dataframe = pd.read_csv(uploaded_file)
        #colum selector
        column = st.selectbox('Choose the column with your URLs:', dataframe.columns)
        
        if source == 'Semrush (Paid)':
            semrush_api_key = st.text_input('API key (Semrush)')
        
        if st.button('Save your data'):

            try:
                st.session_state['semrush_api_key'] = semrush_api_key
            except:
                st.session_state['semrush_api_key'] = None

            st.session_state['country'] = country
            st.session_state['source'] = source
            st.session_state['kws'] = dataframe[column]

            st.write('Data successfully saved! You can now move to step 2 and launch the extraction.')
        

with st.expander('STEP 2: Extract Volume'):
    st.markdown('**You cannot launch this part of the tool without completing step 1 first!! Execution will fail.**')
    if st.button('Launch extraction'):
        #prepare keywords for encoding
        kws = st.session_state['kws']
        kws = kws.str.lower().unique()
        country = st.session_state['country']
        source = st.session_state['source']
        #divide kws into chunks of kws
        chunks = [kws[x:x+50] for x in range(0, len(kws), 50)]
        #create dataframe to receive data from API
        results = pd.DataFrame(columns=['keyword','volume'])

        if source == 'Keyword Surfer (FREE)':
            status_bar = st.progress(0)
            #get search volume data 
            #get data 
            for i in range(0,len(chunks)):
                chunk = chunks[i]
                url = (
                    'https://db2.keywordsur.fr/keyword_surfer_keywords?country={}&keywords=[%22'.format(country)+
                    '%22,%22'.join(chunk)+
                    '%22]'
                )

                r = requests.get(url)
                try:
                    data = json.loads(r.text)
                except:
                    continue

                for key in data.keys():
                    results.loc[len(results)] = [key,data[key]['search_volume']]
                status_bar.progress(i/len(chunks))
            status_bar.progress(100)

            

            results = (
                pd.Series(kws)
                .to_frame()
                .rename({0:'keyword'},axis=1)
                .merge(results,on='keyword',how='left')
                .fillna(0)
            )

            st.download_button(
                "Press to download your data",
                convert_df(results),
                "file.csv",
                "text/csv",
                key='download-csv'
            )
        elif source == 'Semrush (Paid)':
            semrush_api_key = st.session_state['semrush_api_key']
            status_bar = st.progress(0)
            for i in range(len(chunks)):
                chunk = chunks[i]
                url = 'https://api.semrush.com/?type=phrase_these&key={}&export_columns=Ph,Nq&database={}&phrase={}'.format(semrush_api_key,country,';'.join(chunk))
                try:
                    r = requests.get(url)
                    df = pd.read_csv(StringIO(r.text), sep=';')
                    results = pd.concat([results, df.rename({'Keyword':'keyword', 'Search Volume':'volume'}, axis=1)])
                except:
                    continue
                status_bar.progress(i/len(chunks))
            status_bar.progress(100)

            
            results = (
                    pd.Series(kws)
                    .to_frame()
                    .rename({0:'keyword'},axis=1)
                    .merge(results,on='keyword',how='left')
                    .fillna(0)
                    )

            st.download_button(
                        "Press to download your data",
                        convert_df(results),
                        "file.csv",
                        "text/csv",
                        key='download-csv'
                    )
                


                

