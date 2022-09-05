class BuilderBase:
    pass


class PeilbesluitPeil(BuilderBase):
    def __init__(self):
        self.startdatum = datetime.strptime(kwargs.pop("startdatum"), "%Y%m%d")
        self.einddatum = datetime.strptime(kwargs.pop("einddatum"), "%Y%m%d")
        self.eind_winter = kwargs.pop("eind_winter")
        self.begin_zomer = kwargs.pop("begin_zomer")
        self.eind_zomer = kwargs.pop("eind_zomer")
        self.begin_winter = kwargs.pop("begin_winter")
        self.zomerpeil = kwargs.pop("zomerpeil")
        self.winterpeil = kwargs.pop("winterpeil")
        self._2e_marge_onder = kwargs.pop("2e_marge_onder")
        self._1e_marge_onder = kwargs.pop("1e_marge_onder")
        self._1e_marge_boven = kwargs.pop("1e_marge_boven")
        self._2e_marge_boven = kwargs.pop("2e_marge_boven")
