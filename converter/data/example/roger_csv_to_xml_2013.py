# # -*- coding: utf-8 -*-
# """
# Created on Sat Oct 05 00:14:25 2013
#
# @author: Gebruiker
# """
# # benodigde modules
# from datetime import *
#
#
# # open bestanden
# fo_in = open("DOCS-#728510-v1-Template_peilbesluit_invoer_tbv_WIS.csv", "r")
# fo_out = open("PeilbesluitPI_new.xml", "w+")
# # arrays
# series = ["HGTE_PEILBESLUIT", "HGTE_PB_2DOWN", "HGTE_PB_1DOWN", "HGTE_PB_1UP", "HGTE_PB_2UP"]
# description = [
#     "Peilbesluitpeil",
#     "Peilbesluitpeil tweede ondergrens",
#     "Peilbesluitpeil eerste ondergrens",
#     "Peilbesluitpeil eerste bovengrens",
#     "Peilbesluitpeil tweede bovengrens",
# ]
# maanden = ["", "jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
#
# # write top of file
# fo_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
# fo_out.write(
#     '<TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">\n'  # noqa
# )
# fo_out.write("	<timeZone>1.0</timeZone>\n")
#
# # loop read file
# nr = 0
# for line in fo_in:
#     # skip 2 line header
#     if nr > 1:
#         # get variables
#         (
#             pgid,
#             startdatum,
#             einddatum,
#             eind_winter,
#             begin_zomer,
#             eind_zomer,
#             begin_winter,
#             zp,
#             wp,
#             m2down,
#             m1down,
#             m1up,
#             m2up,
#         ) = line[0:-1].split(";")
#         print
#         pgid
#         if startdatum == "":
#             startdatum = "1990-01-01"
#         if einddatum == "":
#             einddatum = "2020-12-31"
#         if eind_winter[-3:] not in maanden:
#             print
#             "ERROR: eind_winter = " + eind_winter
#         if begin_zomer[-3:] not in maanden:
#             print
#             "ERROR: begin_zomer = " + begin_zomer
#         if eind_zomer[-3:] not in maanden:
#             print
#             "ERROR: eind_zomer = " + eind_zomer
#         if begin_winter[-3:] not in maanden:
#             print
#             "ERROR: begin_winter = " + begin_winter
#         zp = float(zp.replace(",", "."))
#         wp = float(wp.replace(",", "."))
#         m2down = float(m2down.replace(",", ".")) / 100
#         m1down = float(m1down.replace(",", ".")) / 100
#         m1up = float(m1up.replace(",", ".")) / 100
#         m2up = float(m2up.replace(",", ".")) / 100
#         # loop write
#         for i in range(5):
#             # write header of series
#             fo_out.write("	<series>\n")
#             fo_out.write("		<header>\n")
#             fo_out.write("			<type>instantaneous</type>\n")
#             fo_out.write("			<locationId>" + str(pgid) + "</locationId>\n")
#             fo_out.write("			<parameterId>" + str(series[i]) + "</parameterId>\n")
#             fo_out.write('			<timeStep unit="nonequidistant"/>\n')
#             fo_out.write('			<startDate date="' + str(startdatum) + '" time="00:00:00"></startDate>\n')
#             fo_out.write('			<endDate date="' + str(einddatum) + '" time="00:00:00"></endDate>\n')
#             fo_out.write("			<missVal>-999.99</missVal>\n")
#             fo_out.write("			<longName>" + str(description[i]) + "</longName>\n")
#             fo_out.write("			<units>mNAP</units>\n")
#             fo_out.write("			<sourceOrganisation></sourceOrganisation>\n")
#             fo_out.write("			<sourceSystem>peilbesluit_invoer_tbv_WIS.csv</sourceSystem>\n")
#             fo_out.write("			<fileDescription></fileDescription>\n")
#             fo_out.write("			<region></region>\n")
#             fo_out.write("		</header>\n")
#
#             # write events of series
#             startjaar, startmaand, startdag = startdatum.split("-")
#             pg_startdatum = date(int(startjaar), int(startmaand), int(startdag))
#             eindjaar, eindmaand, einddag = einddatum.split("-")
#             pg_einddatum = date(int(eindjaar), int(eindmaand), int(einddag))
#             # loop per year
#             for j in range(int(startjaar), int(eindjaar) + 1, 1):
#                 ew_datum = date(int(j), maanden.index(eind_winter[-3:]), int(eind_winter[0:2]))
#                 bz_datum = date(int(j), maanden.index(begin_zomer[-3:]), int(begin_zomer[0:2]))
#                 ez_datum = date(int(j), maanden.index(eind_zomer[-3:]), int(eind_zomer[0:2]))
#                 bw_datum = date(int(j), maanden.index(begin_winter[-3:]), int(begin_winter[0:2]))
#
#                 # HGTE_PEILBESLUIT =
#                 # 1) determine which period counts at startdate
#                 # 2) for each year till year of enddate:
#                 # [[eind_winter,(wp+zp)/2],[begin_zomer,zp],[eind_zomer,(wp+zp)/2],[begin_winter,wp]]
#                 # 3) determine which period counts at enddate
#                 # HGTE_PB_2DOWN =
#                 # 1) determine which period counts at startdate
#                 # 2) for each year till year of enddate:
#                 # [[begin_zomer,zp-m2down],[eind_zomer,wp-m2down]]
#                 # 3) determine which period counts at enddate
#                 # HGTE_PB_1DOWN =
#                 # 1) determine which period counts at startdate
#                 # 2) for each year till year of enddate:
#                 # [[begin_zomer,zp-m1down],[eind_zomer,wp-m1down]]
#                 # 3) determine which period counts at enddate
#                 # HGTE_PB_1UP =
#                 # 1) determine which period counts at startdate
#                 # 2) for each year till year of enddate:
#                 # [[eind_winter,zp+m1up],[begin_winter,wp+m1up]]
#                 # 3) determine which period counts at enddate
#                 # HGTE_PB_2UP =
#                 # 1) determine which period counts at startdate
#                 # 2) for each year till year of enddate:
#                 # [[eind_winter,zp+m2up],[begin_winter,wp+m2up]]
#                 # 3) determine which period counts at enddate
#
#                 # peilbesluit
#                 if i == 0:
#                     if j == int(startjaar):
#                         # event conditions
#                         if pg_startdatum < ew_datum:
#                             startpeil = wp
#                             startnr = 0
#                         elif pg_startdatum < bz_datum:
#                             startpeil = (wp + zp) / 2
#                             startnr = 1
#                         elif pg_startdatum < ez_datum:
#                             startpeil = zp
#                             startnr = 2
#                         elif pg_startdatum < bw_datum:
#                             startpeil = (wp + zp) / 2
#                             startnr = 3
#                         else:
#                             startpeil = wp
#                             startnr = 4
#                         # event reports
#                         fo_out.write(
#                             '		<event date="'
#                             + str(pg_startdatum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(startpeil)
#                             + '" flag="0"/>\n'
#                         )
#                         if startnr < 1:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(ew_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format((wp + zp) / 2)
#                                 + '" flag="0"/>\n'
#                             )
#                         if startnr < 2:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(bz_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(zp)
#                                 + '" flag="0"/>\n'
#                             )
#                         if startnr < 3:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(ez_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format((wp + zp) / 2)
#                                 + '" flag="0"/>\n'
#                             )
#                         if startnr < 4:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(bw_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(wp)
#                                 + '" flag="0"/>\n'
#                             )
#                     elif j == int(eindjaar):
#                         # event conditions
#                         if pg_einddatum > bw_datum:
#                             eindpeil = wp
#                             eindnr = 4
#                         elif pg_einddatum > ez_datum:
#                             eindpeil = (wp + zp) / 2
#                             eindnr = 3
#                         elif pg_einddatum > bz_datum:
#                             eindpeil = zp
#                             eindnr = 2
#                         elif pg_einddatum > ew_datum:
#                             eindpeil = (wp + zp) / 2
#                             eindnr = 1
#                         else:
#                             eindpeil = wp
#                             eindnr = 0
#                         # event reports
#                         if eindnr > 0:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(ew_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format((wp + zp) / 2)
#                                 + '" flag="0"/>\n'
#                             )
#                         if eindnr > 1:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(bz_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(zp)
#                                 + '" flag="0"/>\n'
#                             )
#                         if eindnr > 2:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(ez_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format((wp + zp) / 2)
#                                 + '" flag="0"/>\n'
#                             )
#                         if eindnr > 3:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(bw_datum)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(wp)
#                                 + '" flag="0"/>\n'
#                             )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(pg_einddatum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(eindpeil)
#                             + '" flag="0"/>\n'
#                         )
#                     else:
#                         fo_out.write(
#                             '		<event date="'
#                             + str(ew_datum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format((wp + zp) / 2)
#                             + '" flag="0"/>\n'
#                         )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(bz_datum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(zp)
#                             + '" flag="0"/>\n'
#                         )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(ez_datum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format((wp + zp) / 2)
#                             + '" flag="0"/>\n'
#                         )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(bw_datum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(wp)
#                             + '" flag="0"/>\n'
#                         )
#                 # marges
#                 else:
#                     if i == 1:
#                         marge = -m2down
#                         t1 = bz_datum
#                         t2 = ez_datum
#                     elif i == 2:
#                         marge = -m1down
#                         t1 = bz_datum
#                         t2 = ez_datum
#                     elif i == 3:
#                         marge = m1up
#                         t1 = ew_datum
#                         t2 = bw_datum
#                     elif i == 4:
#                         marge = m2up
#                         t1 = ew_datum
#                         t2 = bw_datum
#                     else:
#                         "ERROR: i = te groot"
#                     if j == int(startjaar):
#                         # event conditions
#                         if pg_startdatum < t1:
#                             startnivo = wp + marge
#                             startnr = 0
#                         elif pg_startdatum < t2:
#                             startnivo = zp + marge
#                             startnr = 1
#                         else:
#                             startnivo = wp + marge
#                             startnr = 2
#                         # event reports
#                         fo_out.write(
#                             '		<event date="'
#                             + str(pg_startdatum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(startnivo)
#                             + '" flag="0"/>\n'
#                         )
#                         if startnr < 1:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(t1)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(zp + marge)
#                                 + '" flag="0"/>\n'
#                             )
#                         if startnr < 2:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(t2)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(wp + marge)
#                                 + '" flag="0"/>\n'
#                             )
#                     elif j == int(eindjaar):
#                         # event conditions
#                         if pg_einddatum > t2:
#                             eindnivo = wp + marge
#                             eindnr = 2
#                         elif pg_einddatum > t1:
#                             eindnivo = zp + marge
#                             eindnr = 1
#                         else:
#                             eindnivo = wp + marge
#                             eindnr = 0
#                         # event reports
#                         if eindnr > 0:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(t1)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(zp + marge)
#                                 + '" flag="0"/>\n'
#                             )
#                         if eindnr > 1:
#                             fo_out.write(
#                                 '		<event date="'
#                                 + str(t2)
#                                 + '" time="00:00:00" value="'
#                                 + "{0:.2f}".format(wp + marge)
#                                 + '" flag="0"/>\n'
#                             )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(pg_einddatum)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(eindnivo)
#                             + '" flag="0"/>\n'
#                         )
#                     else:
#                         fo_out.write(
#                             '		<event date="'
#                             + str(t1)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(zp + marge)
#                             + '" flag="0"/>\n'
#                         )
#                         fo_out.write(
#                             '		<event date="'
#                             + str(t2)
#                             + '" time="00:00:00" value="'
#                             + "{0:.2f}".format(wp + marge)
#                             + '" flag="0"/>\n'
#                         )
#
#             # write footer of series
#             fo_out.write("	</series>\n")
#     # next line
#     nr += 1
#
# # write bottom of file
# fo_out.write("</TimeSeries>\n")
#
# # sluit bestanden
# fo_in.close()
# fo_out.close()
