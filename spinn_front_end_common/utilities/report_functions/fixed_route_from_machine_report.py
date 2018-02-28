import os

from spinn_utilities.progress_bar import ProgressBar


class FixedRouteFromMachineReport(object):
    """ function for writing the fixed routes from the machine
    """

    def __call__(self, transceiver, machine, report_default_directory,
                 app_id):
        """ writing the fixed routes from the machine

        :param transceiver: spinnMan instance
        :param machine: SpiNNMachine instance
        :param report_default_directory: folder where reports reside
        :param loaded_fixed_routes_on_machine_token: \
            Token that states fixed routes have been loaded
        :param app_id: the app id the fixed routes were loaded with
        :rtype: None
        """

        file_name = os.path.join(
            report_default_directory, "fixed_route_routers")

        with open(file_name, "w") as output:
            self._write_fixed_routers(output, transceiver, machine, app_id)

    def _write_fixed_routers(self, f, txrx, machine, app_id):
        """ How to actually describe the fixed routes

        :param f: Where we are writing
        :param txrx: The spinnman transceiver instance
        :param machine: The spinnmanchine instance
        :param app_id: Which app is running on the machine
        :rtype: None
        """
        progress = ProgressBar(machine.n_chips, "Writing fixed route report")
        f.write(" x    y       route         [cores][links]\n")
        for chip in progress.over(machine.chips):
            if not chip.virtual:
                fixed_route = txrx.read_fixed_route(chip.x, chip.y, app_id)
                f.write("{: <3s}:{: <3s} contains route {: <10s} {}\n".format(
                    str(chip.x), str(chip.y),
                    self._reduce_route_value(
                        fixed_route.processor_ids, fixed_route.link_ids),
                    self._expand_route_value(
                        fixed_route.processor_ids, fixed_route.link_ids)))

    @staticmethod
    def _reduce_route_value(processors_ids, link_ids):
        value = 0
        for link in link_ids:
            value += 1 << link
        for processor in processors_ids:
            value += 1 << (processor + 6)
        return str(value)

    @staticmethod
    def _expand_route_value(processors_ids, link_ids):
        """ Convert a 32-bit route word into a string which lists the target\
            cores and links.
        """

        # Convert processor targets to readable values:
        route_string = "["
        separator = ""
        for processor in processors_ids:
            route_string += separator + str(processor)
            separator = ", "

        route_string += "] ["

        # Convert link targets to readable values:
        link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

        separator = ""
        for link in link_ids:
            route_string += separator + link_labels[link]
            separator = ", "
        route_string += "]"
        return route_string
