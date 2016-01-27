from abc import abstractmethod

from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint

from spinn_front_end_common.interface.buffer_management.buffer_models\
    .abstract_receive_buffers_to_host import AbstractReceiveBuffersToHost
from spinn_front_end_common.interface.buffer_management.storage_objects\
    .end_buffering_state import EndBufferingState
from spinn_front_end_common.utilities import exceptions


class ReceiveBuffersToHostBasicImpl(AbstractReceiveBuffersToHost):
    """ This class stores the information required to activate the buffering \
        output functionality for a vertex
    """
    def __init__(self):
        """
        :return: None
        :rtype: None
        """
        self._buffering_output = False
        self._buffering_ip_address = None
        self._buffering_port = None

    def buffering_output(self):
        """ True if the output buffering mechanism is activated

        :return: Boolean indicating whether the output buffering mechanism\
                is activated
        :rtype: bool
        """
        return self._buffering_output

    def set_buffering_output(
            self, buffering_ip_address, buffering_port, board_address=None,
            notification_tag=None):
        """ Activates the output buffering mechanism

        :param buffering_ip_address: IP address of the host which supports\
                the buffering output functionality
        :type buffering_ip_address: string
        :param buffering_port: UDP port of the host which supports\
                the buffering output functionality
        :type buffering_port: int

        :return: None
        :rtype: None
        """
        if not self._buffering_output:
            self._buffering_output = True

            notification_strip_sdp = True

            self.add_constraint(
                TagAllocatorRequireIptagConstraint(
                    buffering_ip_address, buffering_port,
                    notification_strip_sdp, board_address, notification_tag))

            self._buffering_ip_address = buffering_ip_address
            self._buffering_port = buffering_port

    @staticmethod
    def get_buffer_state_region_size(n_buffered_regions):
        """ Get the size of the buffer state region for the given number of\
            buffered regions
        """
        return EndBufferingState.size_of_region(n_buffered_regions)

    @staticmethod
    def get_recording_data_size(n_buffered_regions, schedules):
        """ Get the size of the recording data for the given number of\
            buffered regions and a list of schedules for each region
        """

        schedules_size = sum([8 * len(schedule) for schedule in schedules
                              if schedule is not None])

        # Header info = 4 words = 16 bytes +
        # 2 words = 8 bytes per buffered region (size and schedule size) +
        # The size of the schedules
        return 16 + (n_buffered_regions * 8) + schedules_size

    def reserve_buffer_regions(
            self, spec, state_region, buffer_regions, region_sizes):
        """ Reserves the region for recording and the region for storing the\
            end state of the buffering

        :param spec: The data specification to reserve the region in
        :param state_region: The id of the region to use as the end state\
                region
        :param buffer_regions: The regions ids to reserve for buffering
        :param region_sizes: The sizes of the regions to reserve
        """
        if len(buffer_regions) != len(region_sizes):
            raise exceptions.ConfigurationException(
                "The number of buffer regions must match the number of"
                " regions sizes")
        if self._buffering_output:
            for (buffer_region, region_size) in zip(
                    buffer_regions, region_sizes):
                if region_size > 0:
                    spec.reserve_memory_region(
                        region=buffer_region, size=region_size,
                        label="RECORDING_REGION_{}".format(buffer_region),
                        empty=True)
            spec.reserve_memory_region(
                region=state_region,
                size=EndBufferingState.size_of_region(len(buffer_regions)),
                label='BUFFERED_OUT_STATE', empty=True)

    def get_tag(self, ip_tags):
        """ Finds the tag for buffering from the set of tags presented

        :param ip_tags: A list of ip tags in which to find the tag
        """
        for tag in ip_tags:
            if (tag.ip_address == self._buffering_ip_address and
                    tag.port == self._buffering_port):
                return tag
        return None

    def write_recording_data(
            self, spec, ip_tags, region_sizes, schedules,
            buffer_size_before_receive, time_between_requests=0):
        """ Writes the recording data to the data specification

        :param spec: The data specification to write to
        :param ip_tags: The list of tags assigned to the partitioned vertex
        :param region_sizes: An ordered list of the sizes of the regions in\
                which buffered recording will take place
        :param schedules: An ordered list of lists of tuples of start and end\
                timestamps over which the recording is to be made, or an empty\
                list to record everything
        :param buffer_size_before_receive: The amount of data that can be\
                stored in the buffer before a message is sent requesting the\
                data be read
        :param time_between_requests: The amount of time between requests for\
                more data
        """
        if self._buffering_output:

            # If buffering is enabled, write the tag for buffering
            ip_tag = self.get_tag(ip_tags)
            if ip_tag is None:
                raise Exception(
                    "No tag for output buffering was assigned to this vertex")
            spec.write_value(data=ip_tag.tag)
        else:
            spec.write_value(data=0)
        spec.write_value(data=buffer_size_before_receive)
        spec.write_value(data=time_between_requests)
        for region_size, schedule in zip(region_sizes, schedules):
            spec.write_value(data=region_size)
            if region_size > 0:
                if schedule is not None:
                    spec.write_value(len(schedule))
                    for start, end in schedule:
                        spec.write_value(start)
                        if end is not None:
                            spec.write_value(end)
                        else:
                            spec.write_value(0)
                else:
                    spec.write_value(0)

    @abstractmethod
    def add_constraint(self, constraint):
        pass

    def is_receives_buffers_to_host(self):
        return True