from gobstuf.stuf.brp.base_response import StufResponse


class StufErrorResponse(StufResponse):
    code_path = 'soapenv:Envelope soapenv:Body soapenv:Fault detail'
    string_path = 'soapenv:Envelope soapenv:Body soapenv:Fault faultstring'

    def get_error_code(self):
        error_elm = list(self.stuf_message.find_elm(self.code_path))[0]

        return self.stuf_message.get_elm_value('StUF:stuurgegevens StUF:berichtcode', error_elm)

    def get_error_string(self):
        return self.stuf_message.get_elm_value(self.string_path)
