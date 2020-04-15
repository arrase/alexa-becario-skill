#
# Copyright 2019 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
# These materials are licensed under the Amazon Software License in connection with the Alexa Gadgets Program.
# The Agreement is available at https://aws.amazon.com/asl/.
# See the Agreement for the specific terms and conditions of the Agreement.
# Capitalized terms not defined in this file have the meanings given to them in the Agreement.
#
import logging.handlers
import uuid

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer

from ask_sdk_model.interfaces.custom_interface_controller import (
    SendDirectiveDirective,
    Header,
    Endpoint
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
serializer = DefaultSerializer()
skill_builder = CustomSkillBuilder(api_client=DefaultApiClient())


@skill_builder.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):
    logger.info("== Launch Intent ==")

    response_builder = handler_input.response_builder

    system = handler_input.request_envelope.context.system

    # Get connected gadget endpoint ID.
    endpoints = get_connected_endpoints(handler_input)
    logger.debug("Checking endpoint..")
    if not endpoints:
        logger.debug("No connected gadget endpoints available.")
        return (response_builder
                .speak("No se encontraron gadgets. Inténtalo de nuevo después de conectar tu gadget.")
                .set_should_end_session(True)
                .response)

    endpoint_id = endpoints[0].endpoint_id

    # Store endpoint ID for using it to send custom directives later.
    logger.debug("Received endpoints. Storing Endpoint Id: %s", endpoint_id)
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr['endpointId'] = endpoint_id

    # Send the BlindLEDDirective to make the LED green for 20 seconds.
    return (response_builder
            .speak("Vamos al lío")
            .set_should_end_session(False)
            .response)


@skill_builder.request_handler(can_handle_func=is_intent_name("TVOffIntent"))
def tv_off_intent_handler(handler_input: HandlerInput):
    # Retrieve the stored gadget endpoint ID from the SessionAttributes.
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']

    # Create a token to be assigned to the EventHandler and store it
    # in session attributes for stopping the EventHandler later.
    token = str(uuid.uuid4())
    session_attr['token'] = token

    response_builder = handler_input.response_builder

    # Send the BlindLED Directive to trigger the cycling animation of the LED.
    # and, start a EventHandler for 10 seconds to receive only one
    return (response_builder
            .add_directive(build_send_directive(endpoint_id,'TVOFF'))
            .response)


@skill_builder.request_handler(can_handle_func=is_intent_name("TVOnIntent"))
def tv_on_intent_handler(handler_input: HandlerInput):
    # Retrieve the stored gadget endpoint ID from the SessionAttributes.
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']

    # Create a token to be assigned to the EventHandler and store it
    # in session attributes for stopping the EventHandler later.
    token = str(uuid.uuid4())
    session_attr['token'] = token

    response_builder = handler_input.response_builder

    # Send the BlindLED Directive to trigger the cycling animation of the LED.
    # and, start a EventHandler for 10 seconds to receive only one
    return (response_builder
            .add_directive(build_send_directive(endpoint_id,'TVON'))
            .response)


@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def no_intent_handler(handler_input: HandlerInput):
    logger.info("Received NoIntent..Exiting.")

    # Retrieve the stored gadget endpointId from the SessionAttributes.
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']

    response_builder = handler_input.response_builder

    return (response_builder
            .speak("Deu!")
            .set_should_end_session(True)
            .response)


@skill_builder.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    logger.info("Session ended with reason: " +
                handler_input.request_envelope.request.reason.to_str())
    return handler_input.response_builder.response


@skill_builder.exception_handler(can_handle_func=lambda i, e: True)
def error_handler(handler_input, exception):
    logger.info("==Error==")
    logger.error(exception, exc_info=True)
    return (handler_input.response_builder
            .speak("I'm sorry, something went wrong!").response)


@skill_builder.global_request_interceptor()
def log_request(handler_input):
    # Log the request for debugging purposes.
    logger.info("==Request==\r" +
                str(serializer.serialize(handler_input.request_envelope)))


@skill_builder.global_response_interceptor()
def log_response(handler_input, response):
    # Log the response for debugging purposes.
    logger.info("==Response==\r" + str(serializer.serialize(response)))
    logger.info("==Session Attributes==\r" +
                str(serializer.serialize(handler_input.attributes_manager.session_attributes)))


def get_connected_endpoints(handler_input: HandlerInput):
    return handler_input.service_client_factory.get_endpoint_enumeration_service().get_endpoints().endpoints


def build_send_directive(endpoint_id, directive):
    return SendDirectiveDirective(
        header=Header(namespace='Custom.ShellRunnerGadget', name=directive),
        endpoint=Endpoint(endpoint_id=endpoint_id),
        payload={}
    )


lambda_handler = skill_builder.lambda_handler()
