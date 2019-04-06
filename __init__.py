# coding=utf-8
import spacy
import json
import requests
from contamehistorias.datasources.webarchive import ArquivoPT
from datetime import datetime
from contamehistorias import engine
import os  
from dateutil.relativedelta import relativedelta # $ pip install python-dateutil
from flask import Flask, render_template, send_from_directory
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS


app = Flask(__name__)
api = Api(app)
cors = CORS(app)

domains = ['http://acervo.publico.pt/'
,'http://inimigo.publico.pt/'
,'http://publico.pt/'
,'http://www.dn.pt/'
,'http://dn.sapo.pt/'
,'http://dnoticias.pt/'
,'http://www.rtp.pt/'
,'http://www.cmjornal.pt/'
,'http://www.iol.pt/'
,'http://www.tvi24.iol.pt/'
,'http://noticias.sapo.pt/'
,'http://www.sapo.pt/'
,'http://expresso.sapo.pt/'
,'http://sol.sapo.pt/'
,'http://visao.sapo.pt/'
,'http://exameinformatica.sapo.pt/'
,'http://tek.sapo.pt/'
,'http://www.jornaldenegocios.pt/'
,'http://dinheirodigital.sapo.pt/'
,'http://abola.pt/'
,'http://www.abola.pt/'
,'http://www.jn.pt/'
,'http://jn.pt/'
,'http://sicnoticias.sapo.pt/'
,'http://www.lux.iol.pt/'
,'http://maisfutebol.iol.pt/'
,'http://lux.iol.pt/'
,'http://www.ionline.pt/'
,'http://ionline.sapo.pt/'
,'http://news.google.pt/'
,'http://www.dinheirovivo.pt/'
,'http://www.aeiou.pt/'
,'http://zap.aeiou.pt/'
,'http://www.tsf.pt/'
,'http://meiosepublicidade.pt/'
,'http://www.sabado.pt/'
,'http://www.omirante.pt/'
,'http://www.jb.pt/'
,'http://www.mdb.pt/'
,'http://www.avante.pt/'
,'http://www.oje.pt/'
,'http://www.auniao.pt/'
,'http://www.record.pt/'
,'http://www.ojogo.pt/'
,'http://zerozero.pt/'
,'http://www.maisfutebol.iol.pt/'
,'http://desporto.sapo.pt/'
,'http://jornaleconomico.sapo.pt/'
,'http://www.diarioleiria.pt/'
,'http://www.regiaodeleiria.pt/'
,'http://www.correiodominho.pt/'
,'http://www.diariodominho.pt/'
,'http://economico.sapo.pt/']

params = { 'domains':domains, 
            'from':datetime(year=2010, month=1, day=1), 
            'to':datetime(year=2018, month=12, day=12) }

class Search(Resource):
    def get(self, query):
        #query = 'Cristiano Ronaldo'
        script_dir = os.path.dirname(__file__)
        fileName = 'results/{0}.txt'.format(query)
        fileNameFormated = 'results/{0}-formated.txt'.format(query)
        abs_fileName = os.path.join(script_dir, fileName)
        abs_fileNameFormated = os.path.join(script_dir, fileNameFormated)
        #print(fileName)
        if not(os.path.isfile(abs_fileName)):
            apt =  ArquivoPT()
            search_result = apt.getResult(query=query, **params)

            language = "pt"
            
            cont = engine.TemporalSummarizationEngine()
            intervals = cont.build_intervals(search_result, language)

            f = open(abs_fileName, "w")
            f.write(json.dumps(cont.serialize(intervals)))
            #cont.pprint(intervals)
            f.close()
        else:
            print("Já existe")

        if not(os.path.isfile(abs_fileNameFormated)):
            f = open(abs_fileName, "r") 
            summ_result = json.loads(str(f.read()))
            nlp = spacy.load('pt_core_news_sm')
            newObject = []

            for period in summ_result["results"]:

                #print("--------------------------------")
                #print(period["from"],"until",period["to"])
                result_interval =   {   'from':str(period['from']), 
                                        'to':str(period['to'])
                                    }
                # selected keyphrases
                keyphrases = period["keyphrases"]
                result_interval["headline"] = []
                for keyphrase in keyphrases:  
                    #print(keyphrase["kw"])
                    result_headline = {
                        'headline':str(keyphrase["kw"]),
                        'date':str(keyphrase["date"])
                    }
                    result_headline["persons"] = []
                    doc = nlp(keyphrase["kw"])
                    for ent in doc.ents:
                            if ent.label_ == "PER":
                                #print(ent.text, ent.start_char, ent.end_char, ent.label_)
                                datetime_object = datetime.strptime(str(keyphrase["date"]), '%Y-%m-%d %H:%M:%S')
                                datetime_objectMoreOne = datetime_object + relativedelta(years=+1)
                                api_url_base = 'https://arquivo.pt/imagesearch/?'
                                query1 = ent.text
                                maxItems = 1
                                prettyPrint = 'true'
                                frm = datetime_object.strftime("%Y%m%d%H%M%S")
                                to = datetime_objectMoreOne.strftime("%Y%m%d%H%M%S")
                                size = 'md'
                                api_url = '{0}q={1}&maxItems={2}&prettyPrint={3}&to={4}&from={5}&size={6}'.format(api_url_base,query1,maxItems,prettyPrint,to,frm,size)
                                #print(api_url)
                                response = requests.get(api_url)
                                imgApiResponse = response.json()
                                #print(imgApiResponse)
                                if(len(imgApiResponse["responseItems"]) > 0):
                                    result_chunk =   {   'person':str(ent.text), 
                                                        'start_char':str(ent.start_char),
                                                        'end_char':str(ent.end_char),
                                                        'date':str(keyphrase["date"]),
                                                        'imgSrc':str(imgApiResponse["responseItems"][0]["imgLinkToArchive"])
                                                    }
                                else:
                                    result_chunk =   {   'person':str(ent.text), 
                                                        'start_char':str(ent.start_char),
                                                        'end_char':str(ent.end_char),
                                                        'date':str(keyphrase["date"])
                                                    }
                                result_headline["persons"].append(result_chunk)
                    result_interval["headline"].append(result_headline)
                newObject.append(result_interval)
            #print(json.dumps(newObject[0]))
            f.close()

            f = open(fileNameFormated, "w")
            f.write(json.dumps(newObject))
            return fileNameFormated, 200
                # sources
                # for headline in keyphrase["headlines"]:
                #    print("Date", headline["info"]["datetime"])
                #    print("Source", headline["info"]["domain"])
                #    print("Url", headline["info"]["url"])
                    
                #  print()  
        else:
            return fileNameFormated, 200

@app.route("/")
def root():
    return render_template("index.html")

@app.route('/results/<path:path>')
def send_js(path):
    return send_from_directory('results', path)

api.add_resource(Search, "/query/<string:query>")

if __name__ == "__main__":
    app.run(debug=True)


