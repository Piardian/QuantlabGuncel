package kursiyer;

public class YetiskinOgrenci extends Kursiyer {
    String meslek;
    boolean haftaSonuIstiyor;

    YetiskinOgrenci(String ad, int yas, double kursUcreti, String meslek, boolean haftaSonuIstiyor) {
        this.ad = ad;
        this.yas = yas;
        this.kursUcreti = kursUcreti;
        this.meslek = meslek;
        this.haftaSonuIstiyor = haftaSonuIstiyor;
        kursAdi = "Mesleki Gelisim";
        egitimSeviyesi = "Yetiskin";
        indirimOrani = 0.1;
    }

    String dersProgrami() {
        if (haftaSonuIstiyor) {
            return "Hafta sonu programi";
        }
        return "Hafta ici aksam programi";
    }

    @Override
    String kursiyerBilgileri() {
        return super.kursiyerBilgileri()
             + ", Meslek: " + meslek
             + ", Ders Programi: " + dersProgrami();
    }
}
