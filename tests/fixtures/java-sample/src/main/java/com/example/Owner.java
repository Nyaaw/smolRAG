package com.example;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a pet owner with a collection of pets.
 */
public class Owner {
    private String name;
    private List<Pet> pets;

    /**
     * Constructs a new Owner with an empty pet list.
     *
     * @param name the owner's name
     */
    public Owner(String name) {
        this.name = name;
        this.pets = new ArrayList<>();
    }

    /**
     * Adds a pet to this owner's collection.
     *
     * @param pet the pet to adopt
     */
    public void adopt(Pet pet) {
        pets.add(pet);
    }

    /**
     * Feeds all pets owned by this person.
     */
    public void feedAll() {
        for (Pet pet : pets) {
            if (pet instanceof Dog) {
                Dog dog = (Dog) pet;
                dog.eat();
            } else if (pet instanceof Cat) {
                Cat cat = (Cat) pet;
                cat.eat();
            }
        }
    }

    /**
     * Finds a pet by name.
     *
     * @param name the name to search for
     * @return the matching Pet, or null if not found
     */
    public Pet findPet(String name) {
        for (Pet pet : pets) {
            if (pet.getName().equals(name)) {
                return pet;
            }
        }
        return null;
    }
}
