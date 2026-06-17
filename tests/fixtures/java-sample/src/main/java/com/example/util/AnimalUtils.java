package com.example.util;

import com.example.Animal;
import com.example.Pet;

import java.util.ArrayList;
import java.util.List;

/**
 * Utility methods for working with animals and pets.
 */
public final class AnimalUtils {

    private AnimalUtils() {
        // Utility class should not be instantiated
    }

    /**
     * Produces a human-readable description of an animal.
     *
     * @param animal the animal to describe
     * @return a string describing the animal
     */
    public static String describe(Animal animal) {
        return "Species: " + animal.species + ", Age: " + animal.getAge();
    }

    /**
     * Determines whether a pet is considered a senior.
     *
     * @param pet the pet to evaluate
     * @return true if the pet is 10 years or older
     */
    public static boolean isSenior(Pet pet) {
        return pet.getAge() >= 10;
    }

    /**
     * Filters a list of pets by minimum age.
     *
     * @param pets   the list of pets to filter
     * @param minAge the minimum age (inclusive)
     * @return a new list containing only pets meeting the age criterion
     */
    public static List<Pet> filterByAge(List<Pet> pets, int minAge) {
        List<Pet> result = new ArrayList<>();
        for (Pet pet : pets) {
            if (pet.getAge() >= minAge) {
                result.add(pet);
            }
        }
        return result;
    }
}
