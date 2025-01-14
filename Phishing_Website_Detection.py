# -*- coding: utf-8 -*-
"""Copy of appmlfinal.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19_ebGEawEP6KUda4UJOR3qdwgm3vAboS
"""

import pandas as pd

phish_data=pd.read_csv("/content/online-valid_ds.csv")
phish_data.head()

phish_data.shape

phishurl = phish_data.sample(n = 5000, random_state = 12).copy()
phishurl = phishurl.reset_index(drop=True)
phishurl.head()

phishurl.shape

legit_data = pd.read_csv("/content/Benign_url_file.csv")
legit_data.columns = ['URLs']
legit_data.head()

legit_data.shape

legiturl = legit_data.sample(n = 5000, random_state = 12).copy()
legiturl = legiturl.reset_index(drop=True)
legiturl.head()

legiturl.shape

!pip install dnspython

!pip install python-whois

# Importing required packages
from urllib.parse import urlparse, urlencode
import ipaddress
import re
from bs4 import BeautifulSoup
import whois
import urllib
import urllib.request
from datetime import datetime
import requests
import pandas as pd
import dns.resolver  # Make sure to install the dnspython package

# Define feature extraction functions

# 1. Domain of the URL (Domain)
def getDomain(url):
    domain = urlparse(url).netloc
    if re.match(r"^www.", domain):
        domain = domain.replace("www.", "")
    return domain

# 2. Checks for IP address in URL (Have_IP)
def havingIP(url):
    try:
        ipaddress.ip_address(url)
        ip = 1
    except ValueError:
        ip = 0
    return ip

# 3. Checks the presence of @ in URL (Have_At)
def haveAtSign(url):
    return 1 if "@" in url else 0

# 4. Finding the length of URL and categorizing (URL_Length)
def getLength(url):
    return 0 if len(url) < 54 else 1

# 5. Gives number of '/' in URL (URL_Depth)
def getDepth(url):
    path = urlparse(url).path.split('/')
    return len([segment for segment in path if segment])

# 6. Checking for redirection '//' in the URL (Redirection)
def redirection(url):
    pos = url.rfind('//')
    return 1 if pos > 6 else 0

# 7. Existence of “HTTPS” Token in the Domain Part of the URL (https_Domain)
def httpDomain(url):
    return 1 if 'https' in urlparse(url).netloc else 0

# 8. Checking for Shortening Services in URL (Tiny_URL)
shortening_services = re.compile(
    r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|"
    r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|"
    r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|"
    r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|"
    r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|"
    r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|"
    r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|"
    r"tr\.im|link\.zip\.net"
)

def tinyURL(url):
    return 1 if shortening_services.search(url) else 0

# 9. Checking for Prefix or Suffix Separated by (-) in the Domain (Prefix/Suffix)
def prefixSuffix(url):
    return 1 if '-' in urlparse(url).netloc else 0

# 10. DNS Record Check (DNS_Record)
def dnsRecord(domain):
    try:
        dns.resolver.resolve(domain, 'A')
        return 0
    except dns.resolver.NXDOMAIN:
        return 1
    except dns.resolver.NoAnswer:
        return 1
    except dns.resolver.NoNameservers:
        return 1
    except dns.exception.Timeout:
        return 1
    except Exception:
        return 1

# 12. Web traffic (Web_Traffic)
def web_traffic(url):
    try:
        url = urllib.parse.quote(url)
        rank = BeautifulSoup(
            urllib.request.urlopen(f"http://data.alexa.com/data?cli=10&dat=s&url={url}").read(),
            "xml"
        ).find("REACH")['RANK']
        rank = int(rank)
        return 1 if rank < 100000 else 0
    except (TypeError, urllib.error.URLError):
        return 1

# 13. Survival time of domain: The difference between termination time and creation time (Domain_Age)
def domainAge(domain_name):
    creation_date = domain_name.creation_date
    expiration_date = domain_name.expiration_date

    if isinstance(creation_date, list):
        creation_date = creation_date[0]  # Take the first element if it's a list

    if isinstance(expiration_date, list):
        expiration_date = expiration_date[0]  # Take the first element if it's a list

    if isinstance(creation_date, str):
        try:
            creation_date = datetime.strptime(creation_date, '%Y-%m-%d')
        except:
            return 1

    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except:
            return 1

    if not creation_date or not expiration_date:
        return 1

    age_of_domain = abs((expiration_date - creation_date).days)
    return 1 if age_of_domain / 30 < 6 else 0

# 14. End time of domain: The difference between termination time and current time (Domain_End)
def domainEnd(domain_name):
    expiration_date = domain_name.expiration_date

    if isinstance(expiration_date, list):
        expiration_date = expiration_date[0]  # Take the first element if it's a list

    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except:
            return 1

    if not expiration_date:
        return 1

    today = datetime.now()
    end = abs((expiration_date - today).days)
    return 0 if end / 30 < 6 else 1

# 15. IFrame Redirection (iFrame)
def iframe(response):
    if not response:
        return 1
    return 0 if re.findall(r"[<iframe>|<frameBorder>]", response.text) else 1

# 16. Checks the effect of mouse over on status bar (Mouse_Over)
def mouseOver(response):
    if not response:
        return 1
    return 1 if re.findall("<script>.+onmouseover.+</script>", response.text) else 0

# 17. Checks the status of the right click attribute (Right_Click)
def rightClick(response):
    if not response:
        return 1
    return 0 if re.findall(r"event.button ?== ?2", response.text) else 1

# 18. Checks the number of forwardings (Web_Forwards)
def forwarding(response):
    if not response:
        return 1
    return 0 if len(response.history) <= 2 else 1

legiturl.shape

legiturl.columns

def featureExtractions(url):
    features = []
    features.append(getDomain(url))
    features.append(havingIP(url))
    features.append(haveAtSign(url))
    features.append(getLength(url))
    features.append(getDepth(url))
    features.append(redirection(url))
    features.append(httpDomain(url))
    features.append(tinyURL(url))
    features.append(prefixSuffix(url))

    dns = 0
    try:
        domain_name = whois.whois(urlparse(url).netloc)
    except:
        dns = 1

    features.append(dns)
    features.append(web_traffic(url))
    features.append(1 if dns == 1 else domainAge(domain_name))
    features.append(1 if dns == 1 else domainEnd(domain_name))

    try:
        response = requests.get(url)
    except:
        response = ""
    features.append(iframe(response))
    features.append(mouseOver(response))
    features.append(rightClick(response))
    features.append(forwarding(response))
    features.append(0)

    return features

def featureExtractions(url):
    features = []
    features.append(getDomain(url))
    features.append(havingIP(url))
    features.append(haveAtSign(url))
    features.append(getLength(url))
    features.append(getDepth(url))
    features.append(redirection(url))
    features.append(httpDomain(url))
    features.append(tinyURL(url))
    features.append(prefixSuffix(url))

    dns = 0
    try:
        domain_name = whois.whois(urlparse(url).netloc)
    except:
        dns = 1

    features.append(dns)
    features.append(web_traffic(url))
    features.append(1 if dns == 1 else domainAge(domain_name))
    features.append(1 if dns == 1 else domainEnd(domain_name))

    try:
        response = requests.get(url)
    except:
        response = ""
    features.append(iframe(response))
    features.append(mouseOver(response))
    features.append(rightClick(response))
    features.append(forwarding(response))
    features.append(0)

    return features

features_list = []
labels=[]

for url in legiturl['URLs']:
    features = featureExtractions(url)
    if features:
        features_list.append(features)
        labels.append(0)

feature_names = ['Domain', 'Have_IP', 'Have_At', 'URL_Length', 'URL_Depth','Redirection',
                'https_Domain', 'Prefix/Suffix', 'TinyURL', 'DNS_Record', 'Web_Traffic', 'Domain_Age', 'Domain_End',
                 'iFrame', 'Mouse_Over','Right_Click', 'Web_Forwards', 'Label']

legitimate = pd.DataFrame(features_list, columns= feature_names)
legitimate.to_csv('legit_file.csv', index= False)

phishurl.shape

phish_features = []
label = 1
for i in range(0, 5000):
  url = phishurl['url'][i]
  phish_features.append(featureExtractions(url,label))

feature_names = ['Domain', 'Have_IP', 'Have_At', 'URL_Length', 'URL_Depth','Redirection',
                      'https_Domain', 'TinyURL', 'DNS_Record', 'Domain_Age', 'Domain_End']
phishing = pd.DataFrame(phish_features, columns= feature_names)
urldata = pd.concat([legitimate, phishing]).reset_index(drop=True)
urldata.to_csv('urldata.csv', index=False)

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

df=pd.read_csv("/content/urldata.csv")
df.head()

df.tail()

df.info()

df.describe()

df.count()

df.shape

df.columns

"""VISUALIZING THE DATA

"""

df.hist(bins = 50,figsize = (15,15))
plt.show()

numeric_df = df.select_dtypes(include=[np.number])

# Correlation heatmap for numeric columns
plt.figure(figsize=(15, 13))
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Heatmap')
plt.show()

from pandas.plotting import scatter_matrix
attributes = ['Domain', 'Have_IP', 'Have_At', 'URL_Length', 'URL_Depth','Redirection',
                'https_Domain', 'Prefix/Suffix', 'TinyURL', 'DNS_Record', 'Web_Traffic', 'Domain_Age', 'Domain_End',
                 'iFrame', 'Mouse_Over','Right_Click', 'Web_Forwards', 'Label']
scatter_matrix(df[attributes], figsize=(24, 16))

"""dropping the domain column"""

dfsa=df.drop(['Domain'], axis = 1).copy()

dfsa.columns

"""checking the data for null or missing values"""

dfsa.isnull().sum()

dfsa = dfsa.sample(frac=1).reset_index(drop=True)
dfsa.head()

X = dfsa.drop('Label',axis=1)
y=dfsa['Label']

X.shape

y.shape

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 12)  #test-size 20%
X_train.shape, X_test.shape

from sklearn.metrics import accuracy_score
ML_Model = []
acc_train = []
acc_test = []

def storeResults(model, a,b):
  ML_Model.append(model)
  acc_train.append(round(a, 3))
  acc_test.append(round(b, 3))

from sklearn.tree import DecisionTreeClassifier
tree=DecisionTreeClassifier(max_depth=5)
tree.fit(X_train,y_train)

y_test_tree = tree.predict(X_test)
y_train_tree = tree.predict(X_train)

acc_train_tree = accuracy_score(y_train,y_train_tree)
acc_test_tree = accuracy_score(y_test,y_test_tree)

print("Decision Tree: Accuracy on training Data: {:.3f}".format(acc_train_tree))
print("Decision Tree: Accuracy on test Data: {:.3f}".format(acc_test_tree))

plt.figure(figsize=(9,7))
n_features = X_train.shape[1]
plt.barh(range(n_features), tree.feature_importances_, align='center')
plt.yticks(np.arange(n_features), X_train.columns)
plt.xlabel("Feature importance")
plt.ylabel("Feature")
plt.show()

storeResults('Decision Tree', acc_train_tree, acc_test_tree)

from sklearn.ensemble import RandomForestClassifier

forest = RandomForestClassifier(max_depth=5)
forest.fit(X_train, y_train)

y_test_forest = forest.predict(X_test)
y_train_forest = forest.predict(X_train)

acc_train_forest = accuracy_score(y_train,y_train_forest)
acc_test_forest = accuracy_score(y_test,y_test_forest)

print("Random forest: Accuracy on training Data: {:.3f}".format(acc_train_forest))
print("Random forest: Accuracy on test Data: {:.3f}".format(acc_test_forest))

plt.figure(figsize=(9,7))
n_features = X_train.shape[1]
plt.barh(range(n_features), forest.feature_importances_, align='center')
plt.yticks(np.arange(n_features), X_train.columns)
plt.xlabel("Feature importance")
plt.ylabel("Feature")
plt.show()

storeResults('Random Forest', acc_train_forest, acc_test_forest)

!pip install xgboost

from xgboost import XGBClassifier
xgb = XGBClassifier(learning_rate=0.4,max_depth=7)
xgb.fit(X_train, y_train)

y_test_xgb = xgb.predict(X_test)
y_train_xgb = xgb.predict(X_train)
acc_train_xgb = accuracy_score(y_train,y_train_xgb)
acc_test_xgb = accuracy_score(y_test,y_test_xgb)

print("XGBoost: Accuracy on training Data: {:.3f}".format(acc_train_xgb))
print("XGBoost : Accuracy on test Data: {:.3f}".format(acc_test_xgb))

storeResults('XGBoost', acc_train_xgb, acc_test_xgb)

results = pd.DataFrame({ 'ML Model': ML_Model,
                         'Train Accuracy': acc_train,
                        'Test Accuracy': acc_test})
results
results.sort_values(by=['Test Accuracy', 'Train Accuracy'], ascending=False)

from sklearn.ensemble import VotingClassifier
from sklearn.metrics import classification_report

voting_clf = VotingClassifier(estimators=[
    ('rf', RandomForestClassifier(max_depth=5)),
    ('dt', DecisionTreeClassifier(max_depth=5)),
    ('lr', XGBClassifier(learning_rate=0.4,max_depth=7))
], voting='hard')

voting_clf.fit(X_train, y_train)
y_pred = voting_clf.predict(X_test)
y_pred_train = voting_clf.predict(X_train)
print(f'VotingClassifier Accuracy Train: {accuracy_score(y_train, y_pred_train)}  VotingClassifier Accuracy Test: {accuracy_score(y_test, y_pred)}')
print(classification_report(y_test, y_pred))

import pickle
pickle.dump(xgb, open("XGBoostClassifier.pickle.dat", "wb"))

loaded_model = pickle.load(open("XGBoostClassifier.pickle.dat", "rb"))
loaded_model

!pip install python-whois

# Importing required packages
from urllib.parse import urlparse, urlencode
import ipaddress
import re
from bs4 import BeautifulSoup
import whois
import urllib
import urllib.request
from datetime import datetime
import requests
import pandas as pd
import dns.resolver  # Make sure to install the dnspython package

# Define feature extraction functions
# 1. Domain of the URL (Domain)
def getDomain(url):
    domain = urlparse(url).netloc
    if re.match(r"^www.", domain):
        domain = domain.replace("www.", "")
    return domain

# 2. Checks for IP address in URL (Have_IP)
def havingIP(url):
    try:
        ipaddress.ip_address(url)
        ip = 1
    except ValueError:
        ip = 0
    return ip

# 3. Checks the presence of @ in URL (Have_At)
def haveAtSign(url):
    return 1 if "@" in url else 0

# 4. Finding the length of URL and categorizing (URL_Length)
def getLength(url):
    return 0 if len(url) < 54 else 1

# 5. Gives number of '/' in URL (URL_Depth)
def getDepth(url):
    path = urlparse(url).path.split('/')
    return len([segment for segment in path if segment])

# 6. Checking for redirection '//' in the URL (Redirection)
def redirection(url):
    pos = url.rfind('//')
    return 1 if pos > 6 else 0

# 7. Existence of “HTTPS” Token in the Domain Part of the URL (https_Domain)
def httpDomain(url):
    return 1 if 'https' in urlparse(url).netloc else 0

# 8. Checking for Shortening Services in URL (Tiny_URL)
shortening_services = re.compile(
    r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|"
    r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|"
    r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|"
    r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|"
    r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|"
    r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|"
    r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|"
    r"tr\.im|link\.zip\.net"
)

def tinyURL(url):
    return 1 if shortening_services.search(url) else 0

# 9. Checking for Prefix or Suffix Separated by (-) in the Domain (Prefix/Suffix)
def prefixSuffix(url):
    return 1 if '-' in urlparse(url).netloc else 0

# 10. DNS Record Check (DNS_Record)
def dnsRecord(domain):
    try:
        dns.resolver.resolve(domain, 'A')
        return 0
    except dns.resolver.NXDOMAIN:
        return 1
    except dns.resolver.NoAnswer:
        return 1
    except dns.resolver.NoNameservers:
        return 1
    except dns.exception.Timeout:
        return 1
    except Exception:
        return 1

# 12. Web traffic (Web_Traffic)
def web_traffic(url):
    try:
        url = urllib.parse.quote(url)
        rank = BeautifulSoup(
            urllib.request.urlopen(f"http://data.alexa.com/data?cli=10&dat=s&url={url}").read(),
            "xml"
        ).find("REACH")['RANK']
        rank = int(rank)
        return 1 if rank < 100000 else 0
    except (TypeError, urllib.error.URLError):
        return 1

# 13. Survival time of domain: The difference between termination time and creation time (Domain_Age)
# def domainAge(domain_name):
#     creation_date = domain_name.creation_date
#     expiration_date = domain_name.expiration_date
#     if isinstance(creation_date, str) or isinstance(expiration_date, str):
#         try:
#             creation_date = datetime.strptime(creation_date, '%Y-%m-%d')
#             expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
#         except:
#             return 1
#     if not creation_date or not expiration_date:
#         return 1
#     age_of_domain = abs((expiration_date - creation_date).days)
#     return 1 if age_of_domain / 30 < 6 else 0

# # 14. End time of domain: The difference between termination time and current time (Domain_End)
# def domainEnd(domain_name):
#     expiration_date = domain_name.expiration_date
#     if isinstance(expiration_date, str):
#         try:
#             expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
#         except:
#             return 1
#     if not expiration_date:
#         return 1
#     today = datetime.now()
#     end = abs((expiration_date - today).days)
#     return 0 if end / 30 < 6 else 1
from datetime import datetime

# 13. Survival time of domain: The difference between termination time and creation time (Domain_Age)
def domainAge(domain_name):
    creation_date = domain_name.creation_date
    expiration_date = domain_name.expiration_date

    if isinstance(creation_date, list):
        creation_date = creation_date[0]  # Take the first element if it's a list

    if isinstance(expiration_date, list):
        expiration_date = expiration_date[0]  # Take the first element if it's a list

    if isinstance(creation_date, str):
        try:
            creation_date = datetime.strptime(creation_date, '%Y-%m-%d')
        except:
            return 1

    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except:
            return 1

    if not creation_date or not expiration_date:
        return 1

    age_of_domain = abs((expiration_date - creation_date).days)
    return 1 if age_of_domain / 30 < 6 else 0

# 14. End time of domain: The difference between termination time and current time (Domain_End)
def domainEnd(domain_name):
    expiration_date = domain_name.expiration_date

    if isinstance(expiration_date, list):
        expiration_date = expiration_date[0]  # Take the first element if it's a list

    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except:
            return 1

    if not expiration_date:
        return 1

    today = datetime.now()
    end = abs((expiration_date - today).days)
    return 0 if end / 30 < 6 else 1


# 15. IFrame Redirection (iFrame)
def iframe(response):
    if not response:
        return 1
    return 0 if re.findall(r"[<iframe>|<frameBorder>]", response.text) else 1

# 16. Checks the effect of mouse over on status bar (Mouse_Over)
def mouseOver(response):
    if not response:
        return 1
    return 1 if re.findall("<script>.+onmouseover.+</script>", response.text) else 0

# 17. Checks the status of the right click attribute (Right_Click)
def rightClick(response):
    if not response:
        return 1
    return 0 if re.findall(r"event.button ?== ?2", response.text) else 1

# 18. Checks the number of forwardings (Web_Forwards)
def forwarding(response):
    if not response:
        return 1
    return 0 if len(response.history) <= 2 else 1
def featureExtractions(url):

  features = []
  #Address bar based features (9)
  # features.append(getDomain(url))
  features.append(havingIP(url))
  features.append(haveAtSign(url))
  features.append(getLength(url))
  features.append(getDepth(url))
  features.append(redirection(url))
  features.append(httpDomain(url))
  features.append(tinyURL(url))
  features.append(prefixSuffix(url))


  #Domain based features (4)
  dns = 0
  try:
    domain_name = whois.whois(urlparse(url).netloc)
  except:
    dns = 1

  features.append(dns)
  features.append(web_traffic(url))
  features.append(1 if dns == 1 else domainAge(domain_name))
  features.append(1 if dns == 1 else domainEnd(domain_name))

  # HTML & Javascript based features (4)
  try:
    response = requests.get(url)
  except:
    response = ""
  features.append(iframe(response))
  features.append(mouseOver(response))
  features.append(rightClick(response))
  features.append(forwarding(response))
#  features.append(label)

  return features

featureExtractions('http://www.facebook.com/home/service')

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler,LabelEncoder
df=pd.read_csv("/content/urldata.csv")
df.head()
numeric_df = df.select_dtypes(include=[np.number])

# Correlation heatmap for numeric columns
plt.figure(figsize=(15, 13))
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Heatmap')
plt.show()
from pandas.plotting import scatter_matrix
attributes = ['Domain', 'Have_IP', 'Have_At', 'URL_Length', 'URL_Depth','Redirection',
                'https_Domain', 'Prefix/Suffix', 'TinyURL', 'DNS_Record', 'Web_Traffic', 'Domain_Age', 'Domain_End',
                 'iFrame', 'Mouse_Over','Right_Click', 'Web_Forwards', 'Label']
scatter_matrix(df[attributes], figsize=(24, 16))
dfsa=df.drop(['Domain'], axis = 1).copy()
X = dfsa.drop('Label',axis=1)
y=dfsa['Label']