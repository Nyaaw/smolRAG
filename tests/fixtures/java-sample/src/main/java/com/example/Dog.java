package com.example;

/**
 * A dog is a mammal that can be kept as a pet.
 */
public class Dog extends Mammal implements Pet {
    private String name;

    /**
     * Constructs a new Dog.
     *
     * @param name     the dog's name
     * @param age      the age in years
     * @param furColor the colour of the fur
     */
    public Dog(String name, int age, String furColor) {
        super("Canis familiaris", age, furColor);
        this.name = name;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public void makeSound() {
        System.out.println("Woof");
    }

    /**
     * Makes the dog fetch a thrown object.
     */
    public void fetch() {
        System.out.println(name + " fetches the stick");
    }

    @Override
    public String toString() {
        return "Dog{name='" + name + "', age=" + age + ", furColor='" + furColor + "'}";
    }
}
