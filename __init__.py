"""
This module contains functions for interfacing with node-chatgpt-api and possibly other APIs
"""
import aiohttp
from markdown import markdown
from opsdroid.skill import Skill
from opsdroid.matchers import match_catchall


################################################################################
# Helper functions                                                             #
################################################################################
async def get_api_response(question_text, conversation_context, api_params):
    """
    This communicates with the API
    """
    params = api_params['params']
    data = {**params, **conversation_context}
    api_to_use = conversation_context["api_to_use"]
    if "conversation_keys" in api_params:
        conversation_keys = api_params['conversation_keys']
    else:
        conversation_keys = {}
    if "prompt" in api_params:
        prompt = {api_params['prompt']: question_text}
        data = {**prompt, **params, **conversation_context}
    else:
        prompt = question_text
        data = [question_text, {**data}]

    headers = {'Content-type': 'application/json'}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(api_params['api-url'], json=data) as response:
            response_data = await response.json()
    conversation_context = {
        key: response_data[key]
        for key in conversation_keys if key in response_data
    }
    # Some special keys so they don't get lost along the way
    conversation_context["parentMessageId"] = response_data[
        "messageId"] if "messageId" in response_data else None
    conversation_context["api_to_use"] = api_to_use
    return response_data, conversation_context


################################################################################
# Skills                                                                       #
################################################################################
@match_catchall(messages_only=True)
async def api_conversation(opsdroid, config, message):
    """
    Important variables:
    thread_id - identifier of the conversation and matrix's thread ID
        The key for saving and recalling the conversation into/from memory
    conversation_context - what gets saved in opsdroid memory. This
        contains the name of the API (based on which configuration will be
        applied) as well as any variables needed to identify the
        conversation. It does not contain settings themselves.
    question_text - the message as sent to opsdroid, always without the hot-word part

    Objects:
    connector_matrix - the object obtained from opsdroid.get_connector
    """
    # Get connector_matrix object and start the typing notification
    try:
        if message.connector.name == "matrix":
            connector_matrix = opsdroid.get_connector("matrix")
            await connector_matrix.connection.room_typing(message.target,
                                                          typing_state=True)
    except (NameError,KeyError):
        pass

    api_to_use = None

    try:
        if message.connector.name == "matrix" and 'm.relates_to' in message.raw_event['content']:
            # Load conversation_context for current thread_id if it exists
            question_text = message.text
            thread_id = message.raw_event['content']['m.relates_to']['event_id']
            conversation_context = await opsdroid.memory.get(thread_id)
            api_to_use = conversation_context["api_to_use"]
        else:
            # This is a new message, the first word is the hot-word
            hot_word = message.text.split()[0]
            # Then comes the question
            question_text = ' '.join(message.text.split()[1:])
            # Set thread_id for starting a new thread
            thread_id = message.event_id

            for key in config.get("apis"):
                if hot_word == config.get("apis")[key]["hot-word"]:
                    api_to_use = key
                    break
            if api_to_use is None:
                # Nothing matched. End typing notice and quit the script
                if message.connector.name == "matrix":
                    await connector_matrix.connection.room_typing(
                        message.target, typing_state=False)
                return
            # Generate empty conversation_context
            conversation_context = {"api_to_use": api_to_use}
    except (NameError,KeyError):
        pass


    api_params = config.get("apis")[api_to_use]

    # Get response from API
    try:
        # pylint: disable=W0612
        response_data, conversation_context = await get_api_response(
            question_text, conversation_context, api_params)
        response_key = api_params["response"]
        response_value = eval(f"response_data{response_key}")  # pylint: disable=W0123
    except KeyError:
        response_value = "No such response key was found. Check configuration"

    try:
        if message.connector.name == "matrix":
            # Construct and send a response and save conversation context for matrix
            message_dict = {
                "msgtype": "m.text",
                "body": response_value,
                "formatted_body": markdown(response_value,
                                           extensions=['fenced_code']),
                "format": "org.matrix.custom.html",
                "m.relates_to": {
                    "rel_type": "m.thread",
                    "event_id": thread_id,
                }
            }

            await connector_matrix.connection.room_send(message.target,
                                                        "m.room.message",
                                                        message_dict)
            await connector_matrix.connection.room_typing(message.target,
                                                          typing_state=False)
            await opsdroid.memory.put(thread_id, conversation_context)
        else:
            # For non-matrix connectors send a response
            await message.respond(response_value)

    except (NameError,KeyError):
        pass
