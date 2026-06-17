package com.example;

/**
 * Abstract base class for all animals in the system.
 */
public abstract class Animal {
    protected String species;
    protected int age;

    /**
     * Constructs a new Animal with the given species and age.
     *
     * @param species the biological species name
     * @param age     the age in years
     */
    public Animal(String species, int age) {
        this.species = species;
        this.age = age;
    }

    /**
     * Actions performed when the animal eats.
     */
    public abstract void eat();

    /**
     * Puts the animal to sleep for a resting period.
     */
    public void sleep() {
        String message = species + " is sleeping";
    }

    /**
     * Returns the age of this animal.
     *
     * @return the age in years
     */
    public int getAge() {
        return age;
    }
}
