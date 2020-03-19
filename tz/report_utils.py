import io

import pandas as pd

class ReportCreator:
    def __init__(self, data):
        self.data = data

    def create_csv(self):
        file_object = io.BytesIO()
        csv = pd.DataFrame(self.data).to_csv(index=False)
        file_object.write(csv.encode())
        file_object.seek(0)
        return file_object
