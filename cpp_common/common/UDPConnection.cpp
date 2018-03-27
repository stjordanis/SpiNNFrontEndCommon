#include "UDPConnection.h"
#include <exception>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <vector>
#include <chrono>

using namespace std;
using namespace std::literals::chrono_literals; // BLACK MAGIC!

// Extra magic for Windows.
static void initSocketLibrary(void) {
    static bool initialised = false;
    if (initialised) {
	return;
    }

#ifdef WIN32
    WSADATA wsaData; // if this doesn't work
    //WSAData wsaData; // then try this instead
#include <UDPConnection.h>
    if (WSAStartup(MAKEWORD(1, 1), &wsaData) != 0) {
        fprintf(stderr, "WSAStartup failed.\n");
        exit(1);
    }
#endif // WIN32
    initialised = true;
}

template<class SockType, class TimeRep, class TimePeriod>
static void setSocketTimeout(
	SockType sock, chrono::duration<TimeRep, TimePeriod> d)
{
#ifdef WIN32
    auto ms = chrono::duration_cast<chrono::milliseconds>(d);
    DWORD timeout = (DWORD) ms.count();
#else
    auto sec = chrono::duration_cast<chrono::seconds>(d);
    struct timeval timeout;
    timeout.tv_sec = sec.count();
    timeout.tv_usec = chrono::duration_cast<chrono::microseconds>(
	    d - sec).count();
#endif
    int err = setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO,
	    (const char*) &timeout, sizeof(timeout));
    if (err < 0) {
	throw "Socket timeout could not be set";
    }
}

UDPConnection::UDPConnection(
        int local_port,
        const char *local_host,
        int remote_port,
        const char *remote_host)
    : local_ip_address(htonl(INADDR_ANY))
{
    initSocketLibrary();
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == 0) {
        throw "Socket could not be created";
    }

    sockaddr local_address;
    if (local_host != NULL && local_host[0] != '\0') {
	local_address = get_address(local_host, local_port);
    } else {
	sockaddr_in *local = (sockaddr_in *) &local_address;
	local->sin_family = AF_INET;
	local->sin_addr.s_addr = htonl(INADDR_ANY);
	local->sin_port = htons(local_port);
    }

    // TODO: What is the correct timeout for a receiver socket?
    setSocketTimeout(sock, 500ms);
    bind(sock, (struct sockaddr *) &local_address, sizeof(local_address));

    can_send = false;
    remote_ip_address = 0;
    this->remote_port = 0;

    if (remote_host != NULL && remote_port != 0) {
        can_send = true;
        this->remote_port = remote_port;
        sockaddr remote_address = get_address(remote_host, remote_port);
        if (connect(sock, &remote_address, sizeof(remote_address)) < 0) {
            throw "Error connecting to remote address";
        }
    }

    sockaddr_in local_inet_addr;
    socklen_t local_address_length = sizeof(local_inet_addr);
    if (getsockname(sock, (struct sockaddr *) &local_inet_addr,
            &local_address_length) < 0) {
        throw "Error getting local socket address";
    }
    this->local_ip_address = local_inet_addr.sin_addr.s_addr;
    this->local_port = ntohs(local_inet_addr.sin_port);
}

int UDPConnection::receive_data(char *data, int length)
{
    int received_length = recv(sock, (char *) data, length, 0);

    if (received_length < 0) {
	if (errno == EWOULDBLOCK || errno == EAGAIN) {
	    received_length = 0;
	} else {
	    throw strerror(errno);
	}
    }
    return received_length;
}

bool UDPConnection::receive_data(vector<uint8_t> &data)
{
    int received_length = recv(sock, (char *) data.data(), data.size(), 0);

    if (received_length < 0) {
	if (errno == EWOULDBLOCK || errno == EAGAIN) {
	    received_length = 0;
	} else {
	    throw strerror(errno);
	}
    }
    data.resize(received_length);
    return received_length > 0;
}

int UDPConnection::receive_data_with_address(
        char *data,
        int length,
        struct sockaddr *address)
{
    int address_length = sizeof(*address);

    int received_length = recvfrom(sock, (char *) data, length, 0, address,
            (socklen_t *) &address_length);
    if (received_length < 0) {
	if (errno == EWOULDBLOCK || errno == EAGAIN) {
	    received_length = 0;
	} else {
	    throw strerror(errno);
	}
    }
    return received_length;
}

bool UDPConnection::receive_data_with_address(
	vector<uint8_t> &data,
        struct sockaddr &address)
{
    int address_length = sizeof(address);
    int received_length = recvfrom(sock, (char *) data.data(), data.size(),
	    0, &address, (socklen_t *) &address_length);
    if (received_length < 0) {
	if (errno == EWOULDBLOCK || errno == EAGAIN) {
	    received_length = 0;
	} else {
	    throw strerror(errno);
	}
    }
    data.resize(received_length);
    return received_length > 0;
}

void UDPConnection::send_data(const char *data, int length)
{
    int a = send(sock, (const char *) data, length, 0);

    if (a < 0) {
        throw "Error sending data";
    }
}

void UDPConnection::send_data(const vector<uint8_t> &data)
{
    int a = send(sock, (const char *) data.data(), data.size(), 0);

    if (a < 0) {
        throw "Error sending data";
    }
}

void UDPConnection::send_message(SDPMessage &message)
{
    vector<uint8_t> buffer;
    message.convert_to_byte_vector(buffer);
    send_data(buffer);
}

void UDPConnection::send_data_to(
	const char *data, int length, const sockaddr *address)
{
    if (sendto(sock, (const char *) data, length, 0,
            (const struct sockaddr *) address, sizeof(*address)) < 0) {
        throw "Error sending data";
    }
}

void UDPConnection::send_data_to(
	const vector<uint8_t> &data, const sockaddr &address)
{
    if (sendto(sock, (const char *) data.data(), data.size(), 0,
            (const struct sockaddr *) &address, sizeof(address)) < 0) {
        throw "Error sending data";
    }
}

uint32_t UDPConnection::get_local_port()
{
    return (uint32_t) local_port;
}

uint32_t UDPConnection::get_local_ip()
{
    return (uint32_t) local_ip_address;
}

UDPConnection::~UDPConnection()
{
    shutdown(sock, SHUT_RDWR);
    close(sock);
}
