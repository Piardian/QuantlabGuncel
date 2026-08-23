package kursiyer;

public class LiseOgrencisi extends Kursiyer {
    String alan;
    double okulOrtalamasi;

    LiseOgrencisi(String ad, int yas, double kursUcreti, String alan, double okulOrtalamasi) {
        this.ad = ad    ;
        this.yas = yas;
        this.kursUcreti = kursUcreti;
        this.alan = alan;
        this.okulOrtalamasi = okulOrtalamasi;
        kursAdi = "Akademik Destek";
        egitimSeviyesi = "Lise";
        indirimOrani = 0.3;
    }

    boolean takviyeGerekliMi() {
        return okulOrtalamasi < 70;
    }

    @Override
    String kursiyerBilgileri() {
        return super.kursiyerBilgileri()
             + ", Alan: " + alan
             + ", Okul Ortalamasi: " + okulOrtalamasi
             + ", Takviye Gerekli mi: " + (takviyeGerekliMi() ? "Evet" : "Hayir");
    }
}
