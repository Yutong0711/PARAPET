package thirdparty.canary;

import java.io.Serializable;
import java.util.Objects;

/**
 * Simulated third-party class with a side effect in hashCode() (canary only).
 * A HashMap rehashes its keys while it is being deserialized, so the side
 * effect runs during readObject even though this class defines no readObject.
 */
public class GadgetB implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String name;

    public GadgetB(String name) {
        this.name = name;
    }

    @Override
    public int hashCode() {
        Canary.fire("GadgetB.hashCode");
        return Objects.hashCode(name);
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof GadgetB && Objects.equals(name, ((GadgetB) o).name);
    }
}
