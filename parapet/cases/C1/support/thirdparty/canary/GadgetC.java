package thirdparty.canary;

import java.io.Serializable;

/** Simulated third-party class with a side effect in readResolve() (canary only). */
public class GadgetC implements Serializable {
    private static final long serialVersionUID = 1L;

    private final int id;

    public GadgetC(int id) {
        this.id = id;
    }

    private Object readResolve() {
        Canary.fire("GadgetC.readResolve");
        return this;
    }
}
