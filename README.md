#Resumen

Cloud TTS es una solución al problema de convertir un texto en PDF a un audiolibro.

Utiliza una imagen de Coqui TTS en Google Cloud para crear multiples Google Cloud run jobs. Estos ultimos, trabajan en segmentos
de texto del PDF y convierten sus respectivas partes a audios WAV. Por ultimo, se almacenan los segmentos de audio en un Google Cloud Bucket, se descargan y se
juntan utilizando Python.

La paralelización, comunicación y unificación del producto fianl se realiza por un nodo maestro que ejecuta el pdfreader2.py.

Por ultimo, el usuario tiene las opciones de controlar:

* El numero de frases que cada Job procesa
* Los nombres de los respectivos trabajos y archivos

Sin embargo, CLOUDTTS siempre intentará escalar al maximo el numero de Jobs dado el numero de frases dividido entre el numero de frases por job. 
Por lo tanto, existe un limite de alrededor de paginas dependiendo del numero de frases que se utilize por Job debido a que Google Cloud limita el numero
de jobs que se pueden crear por minuto.

Para abordar este problema, se puede incrementar el numero de frases por Job ó limitar la cantidad de paginas por minuto que se procesan.

##Instalación

Vas a necesitar un projecto en Google Cloud, un bucket disponible y las credenciales en tu computadora.
Vas a ingresar el ID del projecto, el nombre del bucket donde se va almacenar la data, especificar el nombre del archivo PDF que deseas convertir, el numero de frases por pagina (se recomienda 5-20), el nombre del job (puede ser cualquier frase con tal de que solo exista una vez), y las paginas que quieres convertir a audio (pagina de inicio y pagina de fin). Para ver como ingresar las credenciales necesarias por favor mirar https://developers.google.com/workspace/guides/create-credentials y https://cloud.google.com/docs/authentication/provide-credentials-adc.
```
pip install -r requirements.txt
python pdfreader2.py
```

