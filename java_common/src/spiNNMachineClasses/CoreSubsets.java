package spiNNMachineClasses;

import commonClasses.ChipLocation;
import commonClasses.CoreLocation;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;

/**
 *
 * @author alan
 */
public class CoreSubsets implements Iterable<CoreSubset> {
    private final LinkedHashMap<ChipLocation, CoreSubset> coreSubsets = new LinkedHashMap<>();

    public CoreSubsets(CoreSubsets to_add) {
        for (CoreSubset s : to_add)
            addCoreSubset(s);
    }

    public CoreSubsets() {
    }

    public final void addCoreSubset(CoreSubset coreSubset) {
        /**
         * Add a core subset to the set
         * 
         * @param core_subset:
         *            The core subset to add
         * @return: Nothing is returned
         */
        ChipLocation loc = new ChipLocation(coreSubset.getX(),
                coreSubset.getY());
        if (!coreSubsets.containsKey(loc)) {
            coreSubsets.put(loc, coreSubset);
        } else {
            for (int processorID : coreSubset.getProcessorIDs())
                coreSubsets.get(loc).addProcessor(processorID);
        }
    }

    public void addCoreSubsets(ArrayList<CoreSubset> coreSubsets) {
        /**
         * merges a core subsets into this one
         * 
         * @param core_subsets:
         *            the core subsets to add
         * @return void
         */
        for (CoreSubset coreSubset : coreSubsets)
            this.addCoreSubset(coreSubset);
    }

    public void addProcessor(int x, int y, int processor_id) {
        /**
         * Add a processor on a given chip to the set
         * 
         * @param x:
         *            The x-coordinate of the chip
         * @param y:
         *            The y-coordinate of the chip
         * @param processor_id:
         *            A processor id
         * @return: Nothing is returned
         */
        ChipLocation xy = new ChipLocation(x, y);
        if (!coreSubsets.containsKey(xy)) {
            addCoreSubset(new CoreSubset(x, y, new ArrayList<>()));
            coreSubsets.get(xy).addProcessor(processor_id);
        }
    }

    public boolean isChip(int x, int y) {
        /**
         * Determine if the chip with coordinates (x, y) is in the subset
         * 
         * @param x:
         *            The x-coordinate of a chip
         * @param y:
         *            The y-coordinate of a chip
         * @return: True if the chip with coordinates (x, y) is in the subset
         */
        ChipLocation xy = new ChipLocation(x, y);
        return coreSubsets.containsKey(xy);
    }

    public boolean isCore(int x, int y, int processorID) {
        /**
         * Determine if there is a chip with coordinates (x, y) in the\ subset,
         * which has a core with the given id in the subset
         * 
         * @param x:
         *            The x-coordinate of a chip
         * @param y:
         *            The y-coordinate of a chip
         * @param processorID:
         *            The id of a core
         * @return: Whether there is a chip with coordinates (x, y) in the\
         *          subset, which has a core with the given id in the subset
         */
        ChipLocation xy = new ChipLocation(x, y);
        if (coreSubsets.containsKey(xy)) {
            return coreSubsets.get(xy).contains(processorID);
        }
        return false;
    }

    public Iterator<CoreSubset> getCoreSubsets() {
        /**
         * The one-per-chip subsets
         * 
         * @return: Iterable of core subsets
         */
        return coreSubsets.values().iterator();
    }

    public CoreSubset get_core_subset_for_chip(int x, int y) {
        /**
         * Get the core subset for a chip
         * 
         * @param x:
         *            The x-coordinate of a chip
         * @param y:
         *            The y-coordinate of a chip
         * @return: The core subset of a chip, which will be empty if not added
         */
        ChipLocation xy = new ChipLocation(x, y);
        if (coreSubsets.containsKey(xy)) {
            return coreSubsets.get(xy);
        }
        return new CoreSubset(x, y);
    }

    @Override
    public Iterator<CoreSubset> iterator() {
        return coreSubsets.values().iterator();
    }

    public int size() {
        /**
         * The total number of processors that are in these core subsets
         * 
         * @return n cores
         */
        int sum = 0;
        for (CoreSubset subset : this)
            sum += subset.size();
        return sum;
    }

    public boolean contains(CoreLocation xyp) {
        /**
         * True if the given coordinates are in the set
         * 
         * @param xyp:
         *            core location
         * @return True if the given coordinates are in the set false otherwise
         */
        return isCore(xyp.getX(), xyp.getP(), xyp.getP());
    }

    public boolean contains(ChipLocation xy) {
        /**
         * True if the given coordinates are in the set
         * 
         * @param xy:
         *            chip location
         * @return True if the given coordinates are in the set false otherwise
         */
        return isChip(xy.getX(), xy.getY());
    }

    public CoreSubset get(int x, int y) {
        /**
         * returns the core subset associated with that chip, or null
         * 
         * @param x:
         *            chip x coordinate
         * @param y:
         *            chip y coordinate
         * @return: the CoreSubset of the chip, or null if none exists
         */
        ChipLocation loc = new ChipLocation(x, y);
        if (contains(loc)) {
            return coreSubsets.get(loc);
        }
        return null;
    }

    @Override
    public String toString() {
        /**
         * Human-readable version of the object
         * 
         * @return: string representation of the CoreSubsets
         */
        String output = "";
        for (CoreSubset coreSubset : coreSubsets.values()) {
            output += coreSubset.toString();
        }
        return output;
    }
}
