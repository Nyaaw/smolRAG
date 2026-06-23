package com.example;

public class Main {
    public static void main(String[] args) {
        Cat whiskers = new Cat("Whiskers", 5, "orange");
        Dog rex = new Dog("Rex", 3, "brown");
        Owner alice = new Owner("Alice");
        alice.adopt(whiskers);
        alice.adopt(rex);
        Veterinarian drSmith = new Veterinarian("Dr. Smith", "LIC-1234");

        runScenario(drSmith, alice);
    }

    static void runScenario(Veterinarian vet, Owner owner) {
        Pet pet = owner.findPet("Whiskers");
        if (pet != null) {
            handlePet(vet, pet);
        }
    }

    static void handlePet(Veterinarian vet, Pet pet) {
        if (pet instanceof Cat) {
            Cat cat = (Cat) pet;
            doCheckup(vet, cat);
        }
    }

    static void doCheckup(Veterinarian vet, Cat cat) {
        vet.treat(cat);
        vet.treat((Cat) null);
    }
}
