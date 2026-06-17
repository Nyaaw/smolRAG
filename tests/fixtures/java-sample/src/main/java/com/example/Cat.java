package com.example;

/**
 * A cat is a mammal that can be kept as a pet.
 */
public class Cat extends Mammal implements Pet {
    private String name;

    /**
     * Constructs a new Cat.
     *
     * @param name     the cat's name
     * @param age      the age in years
     * @param furColor the colour of the fur
     */
    public Cat(String name, int age, String furColor) {
        super("Felis catus", age, furColor);
        this.name = name;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public void makeSound() {
        System.out.println("Meow");
    }

    /**
     * Makes the cat scratch a surface.
     */
    public void scratch() {
        System.out.println(name + " scratches the furniture");
    }

    @Override
    public String toString() {
        return "Cat{name='" + name + "', age=" + age + ", furColor='" + furColor + "'}";
    }
}
