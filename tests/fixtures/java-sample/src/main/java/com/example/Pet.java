package com.example;

/**
 * Interface representing a pet with basic identifying and behavioural methods.
 */
public interface Pet {
    /**
     * Returns the name of this pet.
     *
     * @return the pet's name
     */
    String getName();

    /**
     * Returns the age of this pet in years.
     *
     * @return the pet's age
     */
    int getAge();

    /**
     * Produces the characteristic sound of this pet.
     */
    void makeSound();
}
