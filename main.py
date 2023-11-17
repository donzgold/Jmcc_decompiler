from codecs import open
from json import loads
from secrets import choice
from string import ascii_letters,digits
try:
    old_actions = loads(open("data/actions.json", "r+", "UTF-8").read())
    actions = {}
    for i in old_actions:
        actions[i["id"]] = i
    old_actions = None
    actions_map = loads(open("data/actions.map.json", "r+", "UTF-8").read())
except Exception as e:
    print(e)
    input()
    exit()


def random_name():
    alphabet = ascii_letters + digits
    return ''.join(choice(alphabet) for i in range(20))  # for a 20-character password


def fix_variables(text):
    global blacklisted_variables, variables, decompile_file, decompile_text, actions_map, actions
    text = text.replace("`", "")
    new_text = ""
    check_text = ""
    placeholders = {"%var_local(": 1, "%var(": 2, "%var_save(": 3}
    check_placeholders = list(placeholders.keys())
    check_mode = 0
    spaces = 0
    depends = False
    for symbol in text:
        check_text = check_text + symbol
        if check_mode == 0:
            new_check_placeholder = check_placeholders.copy()
            for check_placeholder in check_placeholders:
                if check_placeholder.startswith(check_text):
                    if check_placeholder == check_text:
                        variable_type = placeholders[check_placeholder]
                        if placeholders[check_placeholder] in [1, 2, 3]:
                            check_mode = 1
                            new_text = new_text + "%var("
                            check_text = ""
                            spaces = 0
                            depends = True
                        new_check_placeholder = list(placeholders.keys())
                        break
                else:
                    new_check_placeholder.remove(check_placeholder)
            check_placeholders = new_check_placeholder.copy()
            if len(check_placeholders) == 0:
                new_text = new_text + check_text
                check_text = ""
                check_placeholders = list(placeholders.keys())
        if check_mode == 1:
            if symbol == "(":
                spaces -= 1
            elif symbol == ")":
                spaces += 1
            if spaces == 0:
                check_mode = 0
                variable_name = check_text[:-1]
                if variable_type in [1, 4]:
                    if not variable_name in variables["local"]:
                        variables["local"].append(variable_name)
                if variable_type in [2, 5]:
                    if not variable_name in variables["game"]:
                        variables["game"].append(variable_name)
                if variable_type in [3, 6]:
                    if not variable_name in variables["save"]:
                        variables["save"].append(variable_name)
                new_text = new_text + ")"
                check_text = ""
                check_placeholders = list(placeholders.keys())
    new_text = new_text + check_text
    if new_text == "":
        new_text = "%empty%"
    return new_text, depends


def fix_number(text):
    global blacklisted_variables, variables, decompile_file, decompile_text, actions_map, actions
    if text.startswith("%math("):
        text = text.replace("%math(", "", 1)[:-1]
    new_text = ""
    check_text = ""
    placeholders = {"%var_local(": 1, "%var(": 2, "%var_save(": 3, "%math(": 0, "%length_local(": 4, "%length(": 5,
                    "%length_save(": 6}
    check_placeholders = list(placeholders.keys())
    check_mode = 0
    spaces = 0
    variable_type = 0
    minus_check = 0
    index = 0
    for symbol in text:
        index += 1
        check_text = check_text + symbol
        if check_mode == 0:
            if symbol == "(":
                spaces -= 1
            elif symbol == ")":
                spaces += 1
            if symbol == "-":
                if index != 1:
                    check_text = check_text + "("
                    minus_check += 1
            new_check_placeholder = check_placeholders.copy()
            for check_placeholder in check_placeholders:
                if check_placeholder.startswith(check_text):
                    if check_placeholder == check_text:
                        variable_type = placeholders[check_placeholder]
                        if spaces == 0 and minus_check >= 1:
                            minus_check = 0
                            check_text = check_text + ")" * minus_check
                        if placeholders[check_placeholder] in [1, 2, 3]:
                            check_mode = 1
                            check_text = ""
                            new_text = new_text + "`"
                            spaces = 0
                        elif placeholders[check_placeholder] == 0:
                            check_mode = 0
                            new_text = new_text + "("
                            check_text = ""
                        elif placeholders[check_placeholder] in [4, 5, 6]:
                            check_mode = 2
                            check_text = check_text + "`"
                            spaces = 0
                        new_check_placeholder = list(placeholders.keys())
                        break
                else:
                    new_check_placeholder.remove(check_placeholder)
            check_placeholders = new_check_placeholder.copy()
            if len(check_placeholders) == 0:
                new_text = new_text + check_text
                check_text = ""
                check_placeholders = list(placeholders.keys())
        if check_mode == 1:
            if symbol == "(":
                spaces -= 1
            elif symbol == ")":
                spaces += 1
            if spaces == 0:
                check_mode = 0
                variable_name = check_text[:-1:]
                if variable_type in [1, 4]:
                    if not variable_name in variables["local"]:
                        variables["local"].append(variable_name)
                if variable_type in [2, 5]:
                    if not variable_name in variables["game"]:
                        variables["game"].append(variable_name)
                if variable_type in [3, 6]:
                    if not variable_name in variables["save"]:
                        variables["save"].append(variable_name)
                new_text = new_text + variable_name + "`"
                check_text = ""
                check_placeholders = list(placeholders.keys())
        if check_mode == 2:
            if symbol == "(":
                spaces -= 1
            elif symbol == ")":
                spaces += 1
            if spaces == 0:
                check_mode = 0
                variable_name = check_text[:-1:] + "`)"
                if variable_type in [1, 4]:
                    if not variable_name in variables["local"]:
                        variables["local"].append(variable_name)
                if variable_type in [2, 5]:
                    if not variable_name in variables["game"]:
                        variables["game"].append(variable_name)
                if variable_type in [3, 6]:
                    if not variable_name in variables["save"]:
                        variables["save"].append(variable_name)
                new_text = new_text + variable_name
                check_text = ""
                check_placeholders = list(placeholders.keys())
    new_text = new_text + check_text + ")" * minus_check
    if new_text[0] != "(":
        new_text = "(" + new_text + ")"
    return new_text


def argument(arg_2):
    global blacklisted_variables, variables, decompile_file, decompile_text, actions_map, actions
    if len(arg_2.keys()) == 0:
        return
    if arg_2["type"] == "variable":
        if not arg_2["variable"] in variables[arg_2["scope"]]:
            variables[arg_2["scope"]].append(arg_2["variable"])
        arg = "`" + arg_2["variable"].replace("\\", "\\\\").replace("`", "\\`") + "`"
    elif arg_2["type"] == "enum":
        arg = '"' + arg_2["enum"].replace("\\", "\\\\").replace("\"", "\\\"") + '"'
    elif arg_2["type"] == "text":
        arg = '"' + arg_2["text"].replace("\\", "\\\\").replace("\"", "\\\"") + '"'
    elif arg_2["type"] == "number":
        arg = fix_number(str(arg_2["number"]))
    elif arg_2["type"] == "vector":
        arg = "vector(x=" + str(arg_2["x"]) + ",y=" + str(arg_2["y"]) + ",z=" + str(arg_2["z"]) + ")"
    elif arg_2["type"] == "item":
        arg = "\""
        for symbol in arg_2["item"]:
            arg = arg + "\\" + symbol
        arg = arg + "\""
    elif arg_2["type"] == "game_value":
        if "type" in arg_2["selection"]:
            arg = "value::" + arg_2["game_value"] + "<" + loads(arg_2["selection"])["type"] + ">"
        else:
            arg = "value::" + arg_2["game_value"]
    elif arg_2["type"] == "particle":
        arg = "particle(particle=\"" + arg_2["particle_type"] + "\",count=" + str(arg_2["count"]) + ",spread_x=" + str(
            arg_2["first_spread"]) + ",spread_y=" + str(arg_2["second_spread"]) + ",motion_x=" + str(
            arg_2["x_motion"]) + ",motion_y=" + str(arg_2["y_motion"]) + ",motion_z=" + str(arg_2["z_motion"]) + ")"
    elif arg_2["type"] == "sound":
        arg = "sound(sound=\"" + arg_2["sound"] + "\",volume=" + str(arg_2["volume"]) + ",pitch=" + str(
            arg_2["pitch"]) + ")"
    elif arg_2["type"] == "potion":
        arg = "potion(potion=\"" + arg_2["potion"] + "\",amplifier=" + str(arg_2["amplifier"]) + ",duration=" + str(
            arg_2["duration"]) + ")"
    elif arg_2["type"] == "block":
        arg = '"' + arg_2["block"] + '"'
    elif arg_2["type"] == "array":
        arg = []
        for array_arg in arg_2["values"]:
            array_arg = argument(array_arg)
            if array_arg != None:
                arg.append(array_arg)
        arg = "[" + ",".join(arg) + "]"
    else:
        arg = None
        print(arg_2)
    return arg


def operation_read(operations, spaces):
    global blacklisted_variables, variables, decompile_file, decompile_text, actions_map, actions
    for operation in operations:
        if operation["action"] == "empty":
            continue
        action = actions[operation["action"]]
        if operation["action"] in actions_map.keys():
            action_data = actions_map[operation["action"]]
        else:
            action_data = {}
        arguments = {}
        if "values" in operation.keys():
            for index in range(0, len(operation["values"])):
                arg_name = operation["values"][index]["name"]
                arg_2 = operation["values"][index]["value"]
                arg_2 = argument(arg_2)
                if arg_2 != None:
                    arguments[arg_name] = arg_2
        argument_text = []
        lambd = ""
        if operation["action"].startswith("if"):
            for k, v in arguments.items():
                argument_text.append(k + "=" + v)
            argument_text = ",".join(argument_text)
            if "is_inverted" in operation.keys():
                if operation["is_inverted"] == True:
                    s = "if not (" + action["object"] + "::" + action["name"] + "(" + argument_text + "))"
                else:
                    s = "if (" + action["object"] + "::" + action["name"] + "(" + argument_text + "))"
            else:
                s = "if (" + action["object"] + "::" + action["name"] + "(" + argument_text + "))"
        elif operation["action"] == "else":
            s = "else"
        elif operation["action"] == "control_end_thread":
            s = "break"
        else:
            if "assigning" in action_data.keys():
                if action_data["assigning"] in arguments:
                    assigning = arguments[action_data["assigning"]] + "="
                    arguments.pop(action_data["assigning"])
                else:
                    assigning = random_name()
                    variables["local"].append(assigning)
                    assigning = "`" + assigning + "`="
            else:
                assigning = ""
            if "lambda" in action.keys():
                lambd = []
                for i in action["lambda"]:
                    if not i in arguments:
                        lambd_arg = random_name()
                        blacklisted_variables.add(lambd_arg)
                        variables["local"].append(assigning)
                        lambd_arg = "`" + lambd_arg + "`"
                        lambd.append(lambd_arg)
                    else:
                        lambd.append(arguments[i])
                        blacklisted_variables.add(arguments[i])
                        arguments.pop(i)
                lambd = ",".join(lambd) + " ->"
            for k, v in arguments.items():
                argument_text.append(k + "=" + v)
            argument_text = ",".join(argument_text)
            if "conditional" in action.keys():
                new_operation = operation["conditional"]
                new_action = actions[new_operation["action"]]
                if new_operation["action"] in actions_map.keys():
                    new_action_data = actions_map[new_operation["action"]]
                else:
                    new_action_data = {}
                arguments = {}
                if "values" in new_operation.keys():
                    for index in range(0, len(new_operation["values"])):
                        arg_name = new_operation["values"][index]["name"]
                        arg_2 = new_operation["values"][index]["value"]
                        arguments[arg_name] = argument(arg_2)
                argument_text = []
                for k, v in arguments.items():
                    argument_text.append(k + "=" + v)
                argument_text = ",".join(argument_text)
                if "assigning" in new_action_data.keys():
                    assigning = arguments[new_action_data["assigning"]] + "="
                    arguments.pop(new_action_data["assigning"])
                else:
                    assigning = ""
                if "selection" in new_operation.keys():
                    argument_text = assigning + new_action["object"] + "::" + new_action["name"] + "<" + \
                                    new_operation["selection"]["type"] + ">(" + argument_text + ")"
                else:
                    argument_text = assigning + new_action["object"] + "::" + new_action[
                        "name"] + "(" + argument_text + ")"
            if "selection" in operation.keys():
                s = assigning + action["object"] + "::" + action["name"] + "<" + operation["selection"][
                    "type"] + ">(" + argument_text + ")"
            else:
                s = assigning + action["object"] + "::" + action["name"] + "(" + argument_text + ")"
        if "operations" in operation.keys():
            decompile_text.append("    " * spaces + s + "{" + lambd)
            operation_read(operation["operations"], spaces + 1)
            decompile_text.append("    " * spaces + "}")
        else:
            decompile_text.append("    " * spaces + s)


def file_read(a):
    global blacklisted_variables, variables, decompile_file, decompile_text, actions_map, actions
    variables = {"save": [], "game": [], "local": []}
    blacklisted_variables = set()
    decompile_text = []
    for i in a["handlers"]:
        spaces = 1
        if i["type"] == "event":
            s = "event<" + i['event'] + ">{"
        elif i["type"] == "function":
            s = "function `" + i["name"] + "`(){"
        elif i["type"] == "process":
            s = "process `" + i["name"] + "`(){"
        decompile_text.append(s)
        operation_read(i["operations"], spaces)
        decompile_text.append("}")
    new_variables = set()
    depend_variables = set()
    for i in variables["local"]:
        if not "`" + i + "`" in blacklisted_variables:
            variable_name, variable_depends = fix_variables(i)
            variable_name = "var `" + variable_name + "`"
            if variable_depends == True:
                depend_variables.add(variable_name)
            else:
                new_variables.add(variable_name)
    for i in variables["game"]:
        variable_name, variable_depends = fix_variables(i)
        variable_name = "game var `" + variable_name + "`"
        if variable_depends == True:
            depend_variables.add(variable_name)
        else:
            new_variables.add(variable_name)
    for i in variables["save"]:
        variable_name, variable_depends = fix_variables(i)
        variable_name = "save var `" + variable_name + "`"
        if variable_depends == True:
            depend_variables.add(variable_name)
        else:
            new_variables.add(variable_name)
    new_variables = list(new_variables)
    depend_variables = list(depend_variables)
    new_variables.extend(depend_variables)
    new_variables.extend(decompile_text)
    decompile_text = new_variables
    for i in decompile_text:
        decompile_file.write(i + "\n")
    print("Успешная декомпиляция")

while True:
    file_path = input("Путь к файлу: ")
    try:
        a = loads(open(file_path, "r+", "UTF-8").read())
        decompile_file = open(file_path.removesuffix(".json")+".jc", "w+", "UTF-8")
        file_read(a)
        decompile_file.close()
    except Exception as e:
        print(e)