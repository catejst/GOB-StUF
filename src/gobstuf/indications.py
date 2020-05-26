from abc import ABC, abstractmethod


class Indication(ABC):

    def __init__(self, id=None):
        """
        Register the id in uppercase
        Resolve the id to get the corresponding description
        :param id:
        """
        self.id = (id or "").upper()
        self._description = self.indications.get(self.id)

    @property
    @abstractmethod
    def indications(self):
        pass  # pragma: no cover

    @property
    def identifiers(self):
        return {v: k for k, v in self.indications.items()}

    @property
    def description(self):
        return self._description


class Geslachtsaanduiding(Indication):
    VROUW = 'V'
    MAN = 'M'
    ONBEKEND = 'O'

    @property
    def indications(self):
        return {
            self.VROUW: 'vrouw',
            self.MAN: 'man',
            self.ONBEKEND: 'onbekend'
        }


class AanduidingNaamgebruik(Indication):
    EIGEN = 'E'
    EIGEN_PARTNER = 'N'
    PARTNER = 'P'
    PARTNER_EIGEN = 'V'

    @property
    def indications(self):
        return {
            self.EIGEN: 'eigen',
            self.EIGEN_PARTNER: 'eigen_partner',
            self.PARTNER: 'partner',
            self.PARTNER_EIGEN: 'partner_eigen'
        }


class IncompleteDateIndicator(Indication):
    JAAR_MAAND_EN_DAG_ONBEKEND = 'J2'
    MAAND_EN_DAG_ONBEKEND = 'M'
    DAG_ONBEKEND = 'D'
    DATUM_IS_VOLLEDIG = 'V'

    @property
    def indications(self):
        return {
            self.JAAR_MAAND_EN_DAG_ONBEKEND: 'Jaar, maand en dag onbekend',
            self.MAAND_EN_DAG_ONBEKEND: 'Maand en dag onbekend',
            self.DAG_ONBEKEND: 'Dag onbekend',
            self.DATUM_IS_VOLLEDIG: 'Datum is volledig'
        }

    def is_jaar_known(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND]

    def is_maand_known(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND, self.MAAND_EN_DAG_ONBEKEND]

    def is_dag_known(self):
        return self.id not in [self.JAAR_MAAND_EN_DAG_ONBEKEND, self.MAAND_EN_DAG_ONBEKEND, self.DAG_ONBEKEND]

    def is_datum_complete(self):
        return all([self.is_jaar_known(), self.is_maand_known(), self.is_dag_known()])
