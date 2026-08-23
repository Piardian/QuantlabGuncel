package kursiyer;

public class IlkokulOgrencisi extends Kursiyer {
    String veliAdi;
    int sinifDuzeyi;

    IlkokulOgrencisi(String ad, int yas, double kursUcreti, String veliAdi, int sinifDuzeyi) {
        this.ad = ad;
        this.yas = yas;
        this.kursUcreti = kursUcreti;
        this.veliAdi = veliAdi;
        this.sinifDuzeyi = sinifDuzeyi;
        kursAdi = "Temel Egitim";
        egitimSeviyesi = "Ilkokul";
        indirimOrani = 0.5;
    }

    String veliBilgisi() {
        return "Veli: " + veliAdi;
    }

    @Override
    String kursiyerBilgileri() {
        return super.kursiyerBilgileri()
             + ", Sinif: " + sinifDuzeyi
             + ", " + veliBilgisi();
    }
}
