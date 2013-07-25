#!/usr/bin/python
import socket


try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json



####################### variables begin ########################################
# these parameters should be changed to match the actual environment           #
################################################################################

client_socket_timeout = 6                      # seconds
max_msg_length = 2000000                        # bytes

rosbridge_ip = "localhost"                       # hostname or ip
rosbridge_port = 9090                           # port as integer

service_name = "send_bytes"                   # service name

####################### variables end ##########################################


################################################################################



def request_service():
    service_request_object = { "op" : "call_service",
                               "service": "/"+service_name,
                               "fragment_size": 12,
                               "args": { "count" : 500
                                        }
                              }
    service_request = json.dumps(service_request_object)
    #print "sending JSON-message to rosbridge:", service_request
    sock.send(service_request)

################################################################################


####################### script begin ###########################################
# should not need to be changed (but could be improved ;) )                    #
################################################################################
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                        #connect to rosbridge
    sock.settimeout(client_socket_timeout)
    sock.connect((rosbridge_ip, rosbridge_port))

    request_service()                                                               # send service_request

    incoming = None
    buffer = ""
    done = False
    result = None
    reconstructed = None
    while not done:     # should not need a loop (maximum wait can be set by client_socket_timeout), but since its for test/demonstration only .. leave it as it is for now
        try:
            incoming = sock.recv(max_msg_length)                                    # receive service_response from rosbridge
            if buffer == "":
                buffer = incoming
                if incoming == "":
                    print "closing socket"
                    sock.close()
                    break
            else:
                buffer = buffer + incoming
            #print "incoming:",incoming
            #print "+++++++++++++++++++++"
            #service_response = json.loads(incoming)                                 # service_response contains JSON service response as sent by rosbridge
            #print "response:", service_response
            #print "+++++++++++++++++++++"

            # try to access service_request directly (not fragmented)
            try:
                data_object = json.loads(buffer)
                if data_object["op"] == "service_response":
                    reconstructed = buffer
                    done = True

            except Exception, e:
                print "direct access to JSON failed.."
                print e
                print "buffer:", buffer
                pass


    # TODO: if opcode is fragment --> defragment, else access service request directly
            try:
                print "defragmenting incoming messages"
                #result = json.loads("["+buffer+"]")
                # TODO: allow "}{" in strings!
                result_string = buffer.split("}{")
                #print "split;",result_string
                result = []
                for fragment in result_string:
                    if fragment[0] != "{":
                        fragment = "{"+fragment
                    if fragment[len(fragment)-1] != "}":
                        fragment = fragment + "}"
                    result.append(json.loads(fragment))
                #result = json.loads(str(result_string))
                #print "result:", result
                fragment_count = len(result)
                announced = int(result[0]["total"])
                if fragment_count == announced:
                    # sort fragments
                    sorted_result = [None] * fragment_count
                    unsorted_result = []
                    for fragment in result:
                        unsorted_result.append(fragment)
                        sorted_result[int(fragment["num"])] = fragment
                    #print "unsorted_list:", unsorted_result
                    #print "sorted_list:", sorted_result

                    reconstructed = ''
                    for fragment in sorted_result:
                        reconstructed = reconstructed + fragment["data"]

                    done = True
            except Exception, e:
                #print "===="
                #print "["+buffer+"]"
                #print "###"
                #print e
                #print "###"
                pass

            # don't break after first receive if using fragment_size!
            #break
        except Exception, e:

            pass
#            print "---------------------"
#            print buffer
#            print "---------------------"
#            print "received message length:",  len(incoming)
#            print "Exception occured:"
#            print e
#            print "---------------------"

    #print "result:", result

    #if reconstructed == None:
    #    # TODO: sort before reconstructing!!!
    #    reconstructed = ''
    #    for fragment in result:
    #        print "  ", fragment["data"]
    #        reconstructed = reconstructed + fragment["data"]
    #    print
    #    print "reconstructed message :",reconstructed

    ## TODO: check why json arrives as string!
    #reconstructed = reconstructed.strip('"')
    #print "reconstructed message2:",reconstructed

    returned_data = json.loads(reconstructed)
    if returned_data["values"] == None:
        print "response was None -> service was not available"
    else:
        print "received:"
        print reconstructed
    #print "returned json:", returned_data

    #print
    ##print "received:"
    #print "------------------------------------------------------"
    #print "service response contained: ", len(returned_data["values"]["data"]),"bytes"
    ##for key, value in returned_data.iteritems():
    ##    print key, "(length):", len(value)
    #
    ##answer = returned_data["values"]
    #
    ##print "service_answer:", json.dumps(answer)

    #print "service response received successfully: ",len(returned_data["values"]["data"]),"bytes"
    #print ".",
    

except Exception, e:
    print "ERROR - could not receive service_response"

sock.close()                                                                    # close socket
