from pathlib import Path
import csv


class ConvertCsvToXml:

    def __init__(self, orig_csv_path: Path):
        self.orig_csv_path = orig_csv_path
        self._input_df_orig = None
        self._input_df_validated = None
        self._output_xml_path = None

    def _validate_input_csv(self) -> None:
        pass

    def run(self):
        f = open(file=self.orig_csv_path.as_posix(), mode='r')
        csv_f = csv.reader(f)
        data = []

        for row in csv_f:
            data.append(row)
        f.close()

        # df = pd.read_csv('movies2.csv')
        # header = list(df.columns)

        # def convert_row(row):
        #     str_row = """<%s>%s</%s> \n""" * (len(header) - 1)
        #     str_row = """<%s>%s""" + "\n" + str_row + """</%s>"""
        #     var_values = [list_of_elments[k] for k in range(1, len(header)) for list_of_elments in
        #                   [header, row, header]]
        #     var_values = [header[0], row[0]] + var_values + [header[0]]
        #     var_values = tuple(var_values)
        #     return str_row % var_values
        #
        # text = """<collection shelf="New Arrivals">""" + "\n" + '\n'.join(
        #     [convert_row(row) for row in data[1:]]) + "\n" + "</collection >"
        # print(text)
        # with open('output.xml', 'w') as myfile:
        #     myfile.write(text)



