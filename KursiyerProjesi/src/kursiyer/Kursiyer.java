package kursiyer;

public class Kursiyer {
    String ad, kursAdi, egitimSeviyesi;
    int yas;
    double kursUcreti, indirimOrani;

    double odenecekTutar() {
        return kursUcreti - (kursUcreti * indirimOrani);
    }

    String kursiyerBilgileri() {
        return "Ad: " + ad + ", Yas: " + yas + ", Seviye: " + egitimSeviyesi
             + ", Kurs: " + kursAdi + ", Ucret: " + kursUcreti
             + ", Indirim: %" + (indirimOrani * 100)
             + ", Odenecek Tutar: " + odenecekTutar();
    }
}
