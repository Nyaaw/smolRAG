package com.example;

/**
 * Abstract class representing a mammal, extending {@link Animal}.
 */
public abstract class Mammal extends Animal {
    protected String furColor;

    /**
     * Constructs a new Mammal.
     *
     * @param species  the biological species name
     * @param age      the age in years
     * @param furColor the colour of the fur
     */
    public Mammal(String species, int age, String furColor) {
        super(species, age);
        this.furColor = furColor;
    }

    /**
     * Mammals consume food through their mouth.
     */
    @Override
    public void eat() {
        String message = species + " is eating";
    }

    /**
     * Nurses the young of this mammal.
     */
    public void nurse() {
        String message = species + " is nursing";
    }
}
