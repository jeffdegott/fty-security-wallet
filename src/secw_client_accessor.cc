/*  =========================================================================
    secw_client_accessor - Accessor to return documents from the agent

    Copyright (C) 2019 Eaton

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    =========================================================================
*/

/*
@header
    secw_client_accessor - Accessor to return documents from the agent
@discuss
@end
*/

#include "fty_security_wallet_classes.h"

#include <sys/types.h>
#include <unistd.h>

//Too old glibc :(. <gettid> is available since glibc 2.30
#include <sys/syscall.h>
#define gettid() syscall(SYS_gettid)

#include <iomanip> 
#include <sstream>

#include "secw_helpers.h"

namespace secw
{
  ClientAccessor::ClientAccessor(const ClientId & clientId,
                  uint32_t timeout,
                  const std::string & endPoint):
    m_clientId(clientId),
    m_timeout(timeout),
    m_endPoint(endPoint)
  {}

  ClientAccessor:: ~ClientAccessor()
  {}

  std::vector<std::string> ClientAccessor::sendCommand(const std::string & command, const std::vector<std::string> & frames) const
  {
    mlm_client_t * client = mlm_client_new();

    if(client == NULL)
    {
      mlm_client_destroy(&client);
      throw SecwMalamuteClientIsNullException();
    }

    //create a unique sender id: <clientId>.[thread id in hexa]
    pid_t threadId = gettid();
    
    std::stringstream ss;
    ss << m_clientId << "." << std::setfill('0') << std::setw(sizeof(pid_t)*2) << std::hex << threadId;

    std::string uniqueId = ss.str();
    
    int rc = mlm_client_connect (client, m_endPoint.c_str(), m_timeout, uniqueId.c_str());
    
    if (rc != 0)
    {
      mlm_client_destroy(&client);
      throw SecwMalamuteConnectionFailedException();
    }

    //Prepare the request:
    zmsg_t *request = zmsg_new();
    ZuuidGuard  zuuid(zuuid_new ());
    zmsg_addstr (request, zuuid_str_canonical (zuuid));

    //add the command
    zmsg_addstr (request, command.c_str());

    //add all the extra frames
    for(const std::string & frame : frames )
    {
      zmsg_addstr (request, frame.c_str());
    }

    if(zsys_interrupted)
    {
      zmsg_destroy(&request);
      mlm_client_destroy(&client);
      throw SecwMalamuteInterruptedException();
    }

    //send the message
    mlm_client_sendto (client, SECURITY_WALLET_AGENT, "REQUEST", NULL, m_timeout, &request);

    if(zsys_interrupted)
    {
      zmsg_destroy(&request);
      mlm_client_destroy(&client);
      throw SecwMalamuteInterruptedException();
    }

    //Get the reply
    ZmsgGuard recv(mlm_client_recv (client));
    mlm_client_destroy(&client);

    //Get number of frame all the frame
    size_t numberOfFrame = zmsg_size(recv);

    if(numberOfFrame < 2)
    {
      throw SecwProtocolErrorException("Wrong number of frame");
    }

    //Check the message
    ZstrGuard str(zmsg_popstr (recv));
    if(!streq (str, zuuid_str_canonical (zuuid)))
    {
      throw SecwProtocolErrorException("Mismatch correlation id");
    }

    std::vector<std::string> receivedFrames;

    //we unstack all the other frame starting by the 2rd one.
    for(size_t index = 1; index < numberOfFrame; index++)
    {
      ZstrGuard frame( zmsg_popstr(recv) );
      receivedFrames.push_back( std::string(frame.get()) );
    }

    //check if the first frame we get is an error
    if(receivedFrames[0] == "ERROR")
    {
      //It's an error and we will throw directly the exceptions
      if(receivedFrames.size() == 2)
      {
        SecwException::throwSecwException(receivedFrames.at(1));
      }
      else
      {
        throw SecwProtocolErrorException("Missing data for error");
      }

    }

    return receivedFrames;
  }

} //namespace secw
