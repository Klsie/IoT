import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklear.metrics import accuracy_score, classification_report
import joblib

data ={
    'peso_gato':[4.2,3.9,5.1,4.5,6.0,3.2,5.3,4.0,3.8,4.9],
    'distancia':[12,25,10,30,8,28,9,26,24,11],
    'limpieza':[0,1,0,1,0,1,1,0],
    'needLimpieza':[1,0,1,0,1,0,0,1]
}

df = pd.DataFrame(data)

x = df[['peso_gato','distancia','limpieza']]
y = df['needLimpieza']

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.3,random_state=42)

model = DecisionTreeClassifier(criterion='entropy',max_depth=3,random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Precision del Modelo: ", accuracy_score(y_test,y_pred))
print("\nReporte de Clasificacion:\n",classification_report(y_test,y_pred))

print("\nReglas del arbol de decision:")
print(export_text(model, feature_names=list(X.columns)))

joblib.dump(model, 'modelo_arenero.pkl')