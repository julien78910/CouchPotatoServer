from bs4 import BeautifulSoup
import cookielib
import re
import traceback
import urllib2
import urllib
from StringIO import StringIO
import gzip
import time
import mechanize
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.media._base.providers.nzb.base import NZBProvider
from couchpotato.core.helpers import namer_check
from dateutil.parser import parse


log = CPLog(__name__)

class Base(NZBProvider):
    urls = {
        'test': 'http://www.zone-telechargement.com/',
        'detail': 'http://www.zone-telechargement.com/%s',
        'search': 'http://www.zone-telechargement.com/index.php?',
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None


    def getSearchParams(self, movie, quality):
        results = []
        MovieTitles = movie['info']['titles']
        moviequality = simplifyString(quality['identifier'])
        moviegenre = movie['info']['genres']
        if 'Animation' in moviegenre:
            subcat="2"
        elif 'Documentaire' in moviegenre or 'Documentary' in moviegenre:
            subcat="11"
        else:    
            subcat=""
        if moviequality in ['720p']:
            qualpar="96"
        elif moviequality in ['1080p']:
            qualpar="95"
        elif moviequality in ['dvd-r']:
            qualpar="90"
        else:
            qualpar="2"
        if quality['custom']['3d']==1:
            qualpar="62"
            
        for MovieTitle in MovieTitles:
            try:
                TitleStringReal = str(MovieTitle.encode("latin-1").replace('-',' '))
            except:
                continue
            try:
                results.append(urllib.urlencode( {'q': TitleStringReal, 'catlist[]' : qualpar, 'genrelist[]' : subcat} ) + "&orderby=popular")
                results.append(urllib.urlencode( {'q': simplifyString(unicode(TitleStringReal,"latin-1")), 'catlist[]' : qualpar, 'genrelist[]' : subcat} ) + "&orderby=popular")
            except:
                continue
        
        return results

    def _search(self, movie, quality, results):

        previous_link = []
        searchStrings= self.getSearchParams(movie,quality)
        lastsearch=0
        for searchString in searchStrings:
            actualtime=int(time.time())
            if actualtime-lastsearch<10:
                timetosleep= 10-(actualtime-lastsearch)
                time.sleep(timetosleep)
            URL = self.urls['search']+searchString
                
            data = self.getHTMLData(URL)

            if data:
                      
                try:
                    html = BeautifulSoup(data)

                    result = html.find(class_="sresult").get_text()[1:-10]
                    if result == "" or result == None:
                        nb_result = i = 0
                        
                    else:
                        aux = ""
                        l = []
                        for c in result:
                            aux += c
                            try:
                                l.append(int(aux))
                            except:
                                break
                            
                        nb_result = i = max(l)

                    while i > 0 and nb_result - i < 2:
                        if (nb_result - i)%8 == 0:
                            opener = urllib2.build_opener()
                            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                            html = BeautifulSoup(opener.open(URL + "&search_start=" + str((nb_result - i)/8 + 1)))
                            
                        try:
                            aux = html.find_all(class_='postcat')[(nb_result - i)%8]
                            categorie = aux.find_all('a')[0].get_text()
                            insert = 0
                        
                            if categorie == 'Blu-Ray 1080p/720p':
                                insert = 1
                            if categorie == 'Films':
                                insert = 1
                         
                            if insert == 1 :
                                
                                new = {}
                                age = aux.find_all('span')[-1].get_text()
                                idt = html.find_all(class_="titrearticles")[(nb_result - i)%8].find_all('a')[0]['href'].replace('http://www.zone-telechargement.com/','')
                                name = re.sub('[\t\n]', '', html.find_all(class_="titrearticles")[(nb_result - i)%8].get_text())
                                name = name + " " + re.search("[0-9]{4}", age).group(0) + " " + html.find_all(class_="corps")[(nb_result - i)%8].find_all('span')[1].get_text()
                                
                                log.error("test1")

                                testname=namer_check.correctName(name,movie)
                                
                                if testname==0:
                                    i-=1
                                    continue
                                

                                detail_url = ('http://www.zone-telechargement.com/' + idt)

                                if detail_url in previous_link:
                                    return
                                else:
                                    previous_link.append(detail_url)
                                
                                log.error("test2")
                                page2 = opener.open(detail_url)
                                soup = BeautifulSoup(page2).find(class_="contentl")
                                
                                try:
                                    size = ""
                                    size2 = soup.find_all(text=re.compile('([0-9]+[ ](MO|Mo|MB|Mb|GB|GO|Gb|Go))'))
                                    
                                    for s in size2:
                                        if re.search('[+]|(Mbps|Mb\\s)', s):
                                            i-=1
                                            continue
                                        else:
                                            size = s
                                            break
                                            
                                    size = re.search('([0-9]+[ ](MO|Mo|MB|Mb|GB|GO|Gb|Go))', size).group(0)
                                    if size == "" or size == None:
                                        size = "4000 Mo"
                                except:
                                    size = "4000"
                                    

                                premium = soup.find(text=re.compile("Premium|premium|PREMIUM"))

                                    
                                def extra_check(item):
                                    return True

                                log.error("test3")
                                
                                new['id'] = idt
                                new['name'] = name + ' french'
                                new['detail_url'] = detail_url
                                new['size'] = self.parseSize(str(size))
                                new['age'] = self.ageToDays(age)
                                new['seeders'] = 10
                                new['leechers'] = 10
                                new['extra_check'] = extra_check
                                                    
                                log.error("test4")
                                self.findLink('Uptobox', soup, False, results, new)
                                
                                log.error("test5")
                                self.findLink('Uptobox', premium, True, results, new)
                                
                                log.error("test6")
                                self.findLink('1fichier', soup, False, results, new)
                                

                        except Exception as e:
                            log.error("error 1: %s", e)

                        i-=1

                except AttributeError as e:
                    log.error("attr error: %s", e)
            else:
                log.error("error no data")

    def findLink(self, host, soup, premium, results, new):
        try:
            if premium:
                try:
                    lien = soup.find_next(text=re.compile(host)).find_next(href=True)['href']
                except:
                    return
            else:
                try:
                    l = soup.find_next(href=True)
                    upt = l.find_previous(text=True)
                    if upt != host:
                        lien = l.find_next(text=re.compile(host)).find_next(href=True)['href']
                    else:
                        lien = l['href']
                except:
                    return
            
            new['url'] = lien
            results.append(new)
        except Exception as e:
            log.error("error 2: %s", e)
        
        return
                
    def ageToDays(self, age_str):
        age = 0
        aux = age_str[10:-8]
        mois = 0
        
        if 'Janvier' in aux:
            mois = 1
        elif 'Fevrier' in aux:
            mois = 2
        elif 'Mars' in aux:
            mois = 3
        elif 'Avril' in aux:
            mois = 4
        elif 'Mai' in aux:
            mois = 5
        elif 'Juin' in aux:
            mois = 6
        elif 'Juillet' in aux:
            mois = 7
        elif 'Septembre' in aux:
            mois = 9
        elif 'Octobre' in aux:
            mois = 10
        elif 'Novembre' in aux:
            mois = 11
        elif 'Decembre' in aux:
            mois = 12
        else:
            mois = 8
            
        jour = tryInt(aux[0:1])
        
        annee = tryInt(aux[-4:])
        
        a, m, j, _, _, _, _, _, _ = time.gmtime()
        
        age = (a - annee) * 365 + (m - mois)*30.5 + j - jour

        return tryInt(age)

      
    
config = [{
'name': 'uptobox',
'groups': [
    {
        'tab': 'searcher',
        'list': 'nzb_providers',
        'name': 'uptobox',
        'description': 'See <a href="http://www.uptobox.com/">uptobox</a>',
        'wizard': True,
        'options': [
            {
                'name': 'enabled',
                'type': 'enabler',
                'default': False,
            },
            {
                'name': 'seed_ratio',
                'label': 'Seed ratio',
                'type': 'float',
                'default': 0,
                'description': 'Will not be (re)moved until this seed ratio is met.',
            },
            {
                'name': 'seed_time',
                'label': 'Seed time',
                'type': 'int',
                'default': 0,
                'description': 'Will not be (re)moved until this seed time (in hours) is met.',
            },
            {
                'name': 'extra_score',
                'advanced': True,
                'label': 'Extra Score',
                'type': 'int',
                'default': 2000,
                'description': 'Starting score for each release found via this provider.',
            }
        ],
    },
],
}]
