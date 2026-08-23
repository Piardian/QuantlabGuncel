package kursiyer;

import java.util.Scanner;

public class Main {
    public static void main(String[] args) {

        Scanner scan = new Scanner(System.in);

        System.out.println("Kursiyer Adini Giriniz:");
        String ad = scan.nextLine();

        System.out.println("Kursiyer Yasini Giriniz:");
        int yas = scan.nextInt();

        System.out.println("Kurs Ucretini Giriniz:");
        double ucret = scan.nextDouble();
        scan.nextLine();

        System.out.println("Kursiyer Turunu Seciniz:");
        System.out.println("1- Ilkokul Ogrencisi");
        System.out.println("2- Lise Ogrencisi");
        System.out.println("3- Yetiskin Ogrenci");
        int secim = scan.nextInt();
        scan.nextLine();

        if (secim == 1) {
            System.out.println("Veli Adini Giriniz:");
            String veliAdi = scan.nextLine();

            System.out.println("Sinif Duzeyini Giriniz:");
            int sinifDuzeyi = scan.nextInt();

            IlkokulOgrencisi ilkokul = new IlkokulOgrencisi(ad, yas, ucret, veliAdi, sinifDuzeyi);
            System.out.println(ilkokul.kursiyerBilgileri());
        }
        else if (secim == 2) {
            System.out.println("Alanini Giriniz:");
            String alan = scan.nextLine();

            System.out.println("Okul Ortalamasini Giriniz:");
            double okulOrtalamasi = scan.nextDouble();

            LiseOgrencisi lise = new LiseOgrencisi(ad, yas, ucret, alan, okulOrtalamasi);
            System.out.println(lise.kursiyerBilgileri());
        }
        else if (secim == 3) {
            System.out.println("Meslegini Giriniz:");
            String meslek = scan.nextLine();

            System.out.println("Hafta sonu programi istiyor mu? true/false:");
            boolean haftaSonuIstiyor = scan.nextBoolean();

            YetiskinOgrenci yetiskin = new YetiskinOgrenci(ad, yas, ucret, meslek, haftaSonuIstiyor);
            System.out.println(yetiskin.kursiyerBilgileri());
        }
        else {
            System.out.println("Hatali secim yaptiniz!");
        }

        scan.close();
    }
}
