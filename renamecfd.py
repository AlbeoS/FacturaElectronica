#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# RENAMECFD - Renombra archivos de CFD
# Autor: Ricardo Torres
# email: rictor@cuhrt.com
# blog: htpp://rctorr.wordpress.com
# twitter: @rctorr
#
# Descripción
# Este script ayuda a leer un CFD para despues renombrar el archivo
# de la siguiente manera:
#    _RFCReceptor_Fecha_RFCemisor_serie_folio_subtotal_iva_total_descuento_tipoComprobante_version.xml
#
# RFCReceptor: RFC de quien recibe el cfd/cfdi (opcional)
# Fecha: Fecha en que se generó el comprobante
# RFCemisor: RFC de quien emite el cfd/cfdi
# Serie y Folio: Numero de Serie y folio de la factura
# Subtotal, iva, total: Importes de la factura.
# Descuento: Monto de descuento (Opcional)
# Tipo de comprobante: Ingreso/Egreso
# Version: Version del CFDI
#
# El nombre del xml se proporciona desde la línea de comandos, de tal forma que
# se puede usar en algún otro script para automatizar el proceso.
#
###############################################################################
# TODO:
#   - Separar los tipos de impuestos (IVA e ISR).
#
###############################################################################
#
# 17-07-2014 (@pixelead0)
# - FIXED:
#   - Se arregla el IVA, en algunos XML el atributo 'totalImpuestosTrasladados' está vacío.
# - IMPLEMENT FEATURE:
#   - Se agrega parametro opcional para mostrar la columna de 'DESCUENTO', para las compras que tienen descuentos, por ejemplo una compra en el super con promoción del 2x1.
#   - Se agrega parametro opcional para exportar resultados en un archivo .csv
#
# 25-02-2014 (@pixelead0)
# - FIXES:
#   - Si no existe serie y folio, se dejan los campos vacios.
#   - Se valida el tipo de comprobante; si es 'egreso' los importes se dejan en negativos
#   - Se agrega el campo hora
#   - Se valida que el archivo final no exista.
#   - Si existe un pdf con el mismo nombre que el XML se renombran ambos archivos.
#   -
#
# 17-01-2014
# - Ahora permite indicar archivos con algún path distinto a donde está el
#   script
#
# 16-01-2014
# - Se modifica para que pueda ser utilizado en batch y haceptar comodines
#   en el nombre de archivo
#
# Ver 1.1
# - Se corrige problema con los tags para cfdi
#
# Ver 1.0
# - Se lee el nombre del archivo desde la línea de comando
# - Se leer los atributos del archivo xml
# - Genera el nombre con la sintaxis solicitada
# - Renombra el archivo xml al nuevo nombre
#

import sys
import os
import glob
import csv
from optparse import OptionParser
from xml.dom import minidom


class XmlCFD(object):
    """
       Esta clase se encarga de realizar todas las operaciones relacionadas
       con la manipulación del archivo xml de facturación electrónica
    """
    nomFileXml = ''

    def __init__(self, nomFileXml):
        """ Initialize instance. """
        self.nomFileXml = nomFileXml
        self.atributos = dict()

    def getAtributos(self):
        """ Regresa los atributos necesario para formar el nombre del archivo. """

        if os.path.isfile(self.nomFileXml):
            xmlDoc = minidom.parse(self.nomFileXml)
            nodes = xmlDoc.childNodes
            comprobante = nodes[0]

            compAtrib = dict(comprobante.attributes.items())

            """ Si no cuenta con Serie y Folio se dejan vacios los campos """
            if  'serie' in compAtrib:
                self.atributos['serie'] = compAtrib['serie']
            else:
                self.atributos['serie'] = ""

            if  'folio' in compAtrib:
                self.atributos['folio'] = compAtrib['folio']
            else:
                self.atributos['folio'] = ""


            """ Se valida el tipo de comprobante, en caso de ser 'egreso'
                se agrega signo negativo a los importes.
            """
            self.atributos['TipoDeComprobante'] = compAtrib['TipoDeComprobante']
            if self.atributos['TipoDeComprobante']=='E':
                signo= "-"
            else:
                signo=""


            # Se trunca la parte de la hora de emisión
            self.atributos['Fecha']  = compAtrib['Fecha'][:10]

            # Se extrae la hora y se eliminan los ':' (dos puntos)
            self.atributos['Hora']   = compAtrib['Fecha'][11:19]
            self.atributos['Hora'] = self.atributos['Hora'].replace(":","")

            # self.atributos['fecha'] += compAtrib['fecha'][11:2]
            self.atributos['Total'] = signo+compAtrib['Total']

            # Si la compra tiene descuento, agrega el atributo de descuento.
            if  'Descuento' in compAtrib:
                self.atributos['Descuento'] = "-"+compAtrib['Descuento']
            else:
                self.atributos['Descuento'] = "0"

            self.atributos['SubTotal'] = signo+compAtrib['SubTotal']
            version = compAtrib['Version']

            if version == "1.0" or version == "2.0" or version == "2.2": # CFD
                emisor = comprobante.getElementsByTagName('Emisor')
                receptor = comprobante.getElementsByTagName('Receptor')
                impuestos = comprobante.getElementsByTagName('Impuestos')
            elif version == "3.2" or version == "3.0": # CFDI
                emisor = comprobante.getElementsByTagName('cfdi:Emisor')
                receptor = comprobante.getElementsByTagName('cfdi:Receptor')
                impuestos = comprobante.getElementsByTagName('cfdi:Impuestos')
                impuestos2 = comprobante.getElementsByTagName('cfdi:Traslado')
            elif version == "3.3": # CFDI 2018
                emisor = comprobante.getElementsByTagName('cfdi:Emisor')
                receptor = comprobante.getElementsByTagName('cfdi:Receptor')
                impuestos = comprobante.getElementsByTagName('cfdi:Impuestos')
                impuestos2 = comprobante.getElementsByTagName('cfdi:Traslado')
                # complemento = comprobante.getElementsByTagName('cfdi:Complemento')
            else:
                print
                print "El archivo xml no es una versión válida de cfd!"
                print

            A = emisor[0].getAttribute('Rfc')
            B = emisor[0].getAttribute('Nombre')
            C = receptor[0].getAttribute('Rfc')
            self.atributos['rfc'] = A
            self.atributos['nombre'] = B
            self.atributos['receptorRfc'] = C

            D = impuestos[0].getAttribute('TotalImpuestosTrasladados')
            E = impuestos2[0].getAttribute('Importe')

            if E=="":
                try:
                    self.atributos['iva'] = signo+D
                except:
                    self.atributos['iva'] = '0'
            else:
                self.atributos['iva'] = E
            self.atributos['version'] = version


        return self.atributos

    def rename(self, options):
        """ Renombra el archivo xml de la forma:
                Fecha_RFCemisor_serie_folio_subtotal_iva_total.xml

            Regresa el nuevo nombre del archivo
        """

        self.getAtributos()

        nomFileXmlNew = os.path.dirname(self.nomFileXml)

        # Se separa la extension del nombre del archivo
        nomFileOld =  os.path.splitext(self.nomFileXml)

        #Nombres de los archivos con extension pdf y xml
        nomFilePdfOld = nomFileOld[0]+'.pdf'
        nomFileXmlOld = nomFileOld[0]+'.xml'

        nomFileXmlNew += os.sep if len(nomFileXmlNew) > 0 else ""
        if options.receptorrfc: # Se adiciona sólo si la opción -r está incluida
             nomFileXmlNew += '_'+self.atributos['receptorRfc']
        nomFileXmlNew += '_'+self.atributos['rfc']
        nomFileXmlNew += '_'+self.atributos['Fecha']
        nomFileXmlNew += '_'+self.atributos['Hora']


        nomFileXmlNew += '_'+self.atributos['serie']
        nomFileXmlNew += '_'+self.atributos['folio']


        nomFileXmlNew += '_'+self.atributos['SubTotal']
        nomFileXmlNew += '_'+self.atributos['iva']
        nomFileXmlNew += '_'+self.atributos['Total']

        if options.descuentos: # Se adiciona sólo si la opción -d está incluida
            nomFileXmlNew += '_'+self.atributos['descuento']
        nomFileXmlNew += '_'+self.atributos['TipoDeComprobante']
        nomFileXmlNew += '_'+self.atributos['version']

        #Los nuevos nombres de archivos para pdf y xml
        lineCSV  = nomFileXmlNew
        nomFilePdfNew  = nomFileXmlNew+'_.pdf'
        nomFileXmlNew += '_.xml'

        # Si el XML final ya existe, no se renombra
        if not os.path.isfile(nomFileXmlNew):
            os.rename(nomFileXmlOld, nomFileXmlNew)

        # Se valida que exista un archivo pdf llamado igual que el xml.
        # Si el PDF final ya existe, no se renombra.
        if not os.path.isfile(nomFilePdfNew):
            if os.path.isfile(nomFilePdfOld):
                os.rename(nomFilePdfOld, nomFilePdfNew)

        if options.verbose:
            print self.nomFileXml+" => "+nomFileXmlNew

        # Guarda resultados en un archivo CSV para visualizarlo en una hoja de calculo
        if options.archivoSalida:
            f = open(options.archivoSalida,'a')
            lineCSV = lineCSV.replace("_",",")
            f.write(lineCSV+"\n") # python will convert \n to os.linesep
            f.close() # you can omit in most cases as the destructor will call if

        return nomFileXmlNew

    def createCSV(self):
        """ Genera archivo en formato CSV
            Regresa el nuevo nombre del archivo
        """
        myfile = open('nuevo.csv', 'wb')
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(self.atributos)

        return



def main(argv):

    usage = "%prog [opciones] archivocfd.xml|*.xml"
    add_help_option = False
    parser = OptionParser(usage=usage, add_help_option=add_help_option)

    parser.add_option("-d", "--descuentos", action="store_true",
         help=u"Adiciona el monto de descuento del comprobante")

    parser.add_option("-h", "--help", action="help",
         help=u"muestra este mensaje de ayuda y termina")

    parser.add_option("-o", "--output", dest="archivoSalida",
         help=u"Guarda reporte en archivo CSV", metavar="archivoSalida.csv")

    parser.add_option("-r", "--receptorrfc", action="store_true",
         help=u"Adiciona el rfc del receptor al inicio de cada nombre")

    parser.add_option("-v", "--verbose", action="store_true",
         help=u"Va mostrando la lista de los archivos modificados")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(0)

    # Se obtiene la lista de archivos
    if len(args) == 1 and "*" not in args[0]:
        files = args
    elif len(args) == 1 and "*" in args[0]:
        files = glob.glob(args[0])
    else:
        files = args

    if options.archivoSalida and os.path.isfile(options.archivoSalida):
        os.remove(options.archivoSalida)


    for item in files:
        nomFileXml = item
        if not os.path.isfile(nomFileXml):
            print "El archivo "+nomFileXml+" no existe."
        else:
            xmlcfd = XmlCFD(nomFileXml)
            xmlcfd.rename(options)
            #xmlcfd.createCSV()

if __name__ == "__main__":
  main(sys.argv[1:])

