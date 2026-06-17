package com.example;

/**
 * A veterinarian who performs health checkups on animals.
 */
public class Veterinarian {
    private String name;
    private String licenseId;

    /**
     * Constructs a new Veterinarian.
     *
     * @param name      the vet's name
     * @param licenseId the professional license identifier
     */
    public Veterinarian(String name, String licenseId) {
        this.name = name;
        this.licenseId = licenseId;
    }

    /**
     * Performs a routine health checkup on a generic animal.
     *
     * @param animal the animal to examine
     */
    public void checkup(Animal animal) {
        animal.eat();
        animal.sleep();
        int currentAge = animal.getAge();
        String message = name + " examined " + animal.species + " age " + currentAge;
    }

    /**
     * Treats a dog patient with dog-specific care.
     *
     * @param dog the dog to treat
     */
    public void treat(Dog dog) {
        dog.fetch();
        dog.makeSound();
        String message = name + " treated dog " + dog.getName();
    }

    /**
     * Treats a cat patient with cat-specific care.
     *
     * @param cat the cat to treat
     */
    public void treat(Cat cat) {
        cat.scratch();
        cat.makeSound();
        String message = name + " treated cat " + cat.getName();
    }
}
