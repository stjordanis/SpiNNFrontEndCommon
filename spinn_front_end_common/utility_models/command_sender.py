# pacman imports
from pacman.model.decorators.overrides import overrides
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_key_and_mask_constraint \
    import KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.graphs.application.impl.application_edge import \
    ApplicationEdge
from pacman.model.graphs.application.impl.application_vertex import \
    ApplicationVertex
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.executor.injection_decorator import inject_items

# spinn front end common imports
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models.\
    abstract_vertex_with_dependent_vertices import \
    AbstractVertexWithEdgeToDependentVertices
from spinn_front_end_common.utilities import constants
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models\
    .abstract_binary_uses_simulation_run import AbstractBinaryUsesSimulationRun
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spinn_front_end_common.utility_models.command_sender_machine_vertex \
    import CommandSenderMachineVertex


class CommandSender(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary, AbstractBinaryUsesSimulationRun,
        AbstractProvidesOutgoingPartitionConstraints):
    """ A utility for sending commands to a vertex (possibly an external\
        device) at fixed times in the simulation
    """

    # all commands will use this mask
    _DEFAULT_COMMAND_MASK = 0xFFFFFFFF

    def __init__(self, label, constraints):

        ApplicationVertex.__init__(self, label, constraints, 1)

        self._times_with_commands = dict()
        self._commands_at_start_resume = list()
        self._commands_at_pause_stop = list()
        self._partition_id_to_keys = dict()
        self._keys_to_partition_id = dict()
        self._edge_partition_id_counter = 0
        self._vertex_to_key_map = dict()

    def add_commands(
            self, start_resume_commands, pause_stop_commands,
            timed_commands, vertex_to_add):
        """ Add commands to be sent down a given edge

        :param start_resume_commands: The commands to send at start/resume states
        :type start_resume_commands: iterable of\
                    :py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :param pause_stop_commands: the commands to send at stop/pause states
        :type pause_stop_commands: iterable of\
                    :py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :param timed_commands: The commands to send at arbitary times
        :type timed_commands: iterable of\
                    :py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :param vertex_to_add: The vertex these commands are associatyed with
                              used in the graph for these commands
        :param edge: The edge down which the commands will be sent
        :type edge:\
                    :py:class:`pacman.model.graph.application.abstract_application_edge.AbstractApplicationEdge`
        :raise ConfigurationException:\
            If the edge already has commands or if all the commands masks are\
            not 0xFFFFFFFF and there is no commonality between the\
            command masks
        """

        # container for keys for partition mapping (remove duplicates)
        command_keys = set()
        self._vertex_to_key_map[vertex_to_add] = set()

        # update holders
        self._commands_at_start_resume.extend(start_resume_commands)
        self._commands_at_pause_stop.extend(pause_stop_commands)

        # Go through the timed commands and record their times and track keys
        for command in timed_commands:

            # track times for commands
            if command.time not in self._times_with_commands:
                self._times_with_commands[command.time] = list()
            self._times_with_commands[command.time].append(command)

            # track keys
            command_keys.add(command.key)
            self._vertex_to_key_map[vertex_to_add].add(command.key)

        # track keys from start and resume commands.
        for command in start_resume_commands:
            # track keys
            command_keys.add(command.key)
            self._vertex_to_key_map[vertex_to_add].add(command.key)

        # track keys from pause and stop commands
        for command in pause_stop_commands:
            # track keys
            command_keys.add(command.key)
            self._vertex_to_key_map[vertex_to_add].add(command.key)

        # create mapping between keys and partitions via partition constraint
        for key in command_keys:

            partition_id = "COMMANDS{}".format(self._edge_partition_id_counter)
            self._keys_to_partition_id[key] = partition_id
            self._partition_id_to_keys[partition_id] = key
            self._edge_partition_id_counter += 1

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "n_machine_time_steps": "RunTimeMachineTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "n_machine_time_steps"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
             n_machine_time_steps):
        placement.vertex.generate_data_specification(
            spec, placement, machine_time_step, time_scale_factor,
            n_machine_time_steps)

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        return CommandSenderMachineVertex(
            constraints, resources_required, label, self._times_with_commands,
            self._commands_at_start_resume, self._commands_at_pause_stop)

    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):

        sdram = (
            CommandSenderMachineVertex.get_timed_commands_bytes(
                self._times_with_commands) +
            CommandSenderMachineVertex.get_n_command_bytes(
                self._commands_at_start_resume) +
            CommandSenderMachineVertex.get_n_command_bytes(
                self._commands_at_pause_stop) +
            constants.SYSTEM_BYTES_REQUIREMENT +
            CommandSenderMachineVertex.get_provenance_data_size(0) +
            (CommandSenderMachineVertex.get_number_of_mallocs_used_by_dsg() *
             constants.SARK_PER_MALLOC_SDRAM_USAGE))

        # Return the SDRAM and 1 core
        return ResourceContainer(sdram=SDRAMResource(sdram))

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return 1

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        """ Return a string representation of the models binary

        :return:
        """
        return CommandSenderMachineVertex.get_binary_file_name()

    @overrides(AbstractVertexWithEdgeToDependentVertices.dependent_vertices)
    def dependent_vertices(self):
        return self._vertex_to_key_map.keys()

    def edges_and_partitions(self):
        edges = list()
        partition_ids = list()
        keys_added = set()
        for vertex in self._vertex_to_key_map:
            for key in self._vertex_to_key_map[vertex]:
                if key not in keys_added:
                    keys_added.add(key)
                    app_edge = ApplicationEdge(self, vertex)
                    edges.append(app_edge)
                    partition_ids.append(self._keys_to_partition_id[key])
        print keys_added
        return edges, partition_ids

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        constraints = list()
        constraints.append(KeyAllocatorFixedKeyAndMaskConstraint(
                [BaseKeyAndMask(
                    self._partition_id_to_keys[partition.identifier],
                    self._DEFAULT_COMMAND_MASK)]))
        return constraints