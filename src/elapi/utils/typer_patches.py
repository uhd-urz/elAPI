# Fixes typer not working with optional value
# (that Click supports: https://click.palletsprojects.com/en/8.1.x/options/#optional-value)
# From https://github.com/fastapi/typer/discussions/873, PR 872, and https://stackoverflow.com/a/78226412/7696241.
from typing import (
    Optional,
    Callable,
    Any,
    Sequence,
    List,
    Tuple,
    Union,
    Dict,
)

import click
import typer
from typer.core import TyperOption
from typer.main import (
    lenient_issubclass,
    get_click_type,
    determine_type_convertor,
    generate_tuple_convertor,
    get_command_name,
    get_param_callback,
    get_param_completion,
)
from typer.models import (
    ParamMeta,
    ParameterInfo,
    Required,
    ArgumentInfo,
    OptionInfo,
    NoneType,
)
from typer.utils import get_params_from_function

_original_get_click_param = typer.main.get_click_param
_original_get_params_convertors_ctx_param_name_from_function = (
    typer.main.get_params_convertors_ctx_param_name_from_function
)


def get_params_convertors_ctx_param_name_from_function(
    callback: Optional[Callable[..., Any]],
) -> Tuple[List[Union[click.Argument, click.Option]], Dict[str, Any], Optional[str]]:
    params = []
    convertors = {}
    context_param_name = None
    if callback:
        parameters = get_params_from_function(callback)
        for param_name, param in parameters.items():
            if lenient_issubclass(param.annotation, click.Context):
                context_param_name = param_name
                continue
            try:
                click_param, convertor = _patched_get_click_param(param)
            except TypeError:
                # Because the patched version throws an error when typer.Argument is used
                # TypeError: cannot unpack non-iterable NoneType object
                click_param, convertor = _original_get_click_param(param)
            if convertor:
                convertors[param_name] = convertor
            params.append(click_param)
    return params, convertors, context_param_name


def generate_list_convertor(
    convertor: Optional[Callable[[Any], Any]], default_value: Optional[Any]
) -> Callable[[Sequence[Any]], Optional[List[Any]]]:
    def internal_convertor(value: Sequence[Any]) -> Optional[List[Any]]:
        if default_value is None and len(value) == 0:
            return None
        return [convertor(v) if convertor else v for v in value]

    return internal_convertor


def _patched_get_click_param(
    param: ParamMeta,
) -> Tuple[Union[click.Argument, click.Option], Any]:
    default_value = None
    required = False
    if isinstance(param.default, ParameterInfo):
        parameter_info = param.default
        if parameter_info.default == Required:
            required = True
        else:
            default_value = parameter_info.default
    elif param.default == Required or param.default == param.empty:
        required = True
        parameter_info = ArgumentInfo()
    else:
        default_value = param.default
        parameter_info = OptionInfo()
    annotation: Any = Any
    if not param.annotation == param.empty:
        annotation = param.annotation
    else:
        annotation = str
    main_type = annotation
    is_list = False
    is_tuple = False
    parameter_type: Any = None
    is_flag = None
    origin = getattr(main_type, "__origin__", None)
    if origin is not None:
        # Handle Optional[SomeType]
        if origin is Union:
            types = []
            for type_ in main_type.__args__:
                if type_ is NoneType:
                    continue
                types.append(type_)
            assert len(types) == 1, "Typer Currently doesn't support Union types"
            main_type = types[0]
            origin = getattr(main_type, "__origin__", None)
        # Handle Tuples and Lists
        if lenient_issubclass(origin, List):
            main_type = main_type.__args__[0]
            assert not getattr(
                main_type, "__origin__", None
            ), "List types with complex sub-types are not currently supported"
            is_list = True
        elif lenient_issubclass(origin, Tuple):  # type: ignore
            types = []
            for type_ in main_type.__args__:
                assert not getattr(
                    type_, "__origin__", None
                ), "Tuple types with complex sub-types are not currently supported"
                types.append(
                    get_click_type(annotation=type_, parameter_info=parameter_info)
                )
            parameter_type = tuple(types)
            is_tuple = True
    if parameter_type is None:
        parameter_type = get_click_type(
            annotation=main_type, parameter_info=parameter_info
        )
    convertor = determine_type_convertor(main_type)
    if is_list:
        convertor = generate_list_convertor(
            convertor=convertor, default_value=default_value
        )
    if is_tuple:
        convertor = generate_tuple_convertor(main_type.__args__)
    if isinstance(parameter_info, OptionInfo):
        is_flag = parameter_info.is_flag
        if main_type is bool and is_flag is not False:
            is_flag = True
            # Click doesn't accept a flag of type bool, only None, and then it sets it
            # to bool internally
            parameter_type = None
        default_option_name = get_command_name(param.name)
        if is_flag:
            default_option_declaration = (
                f"--{default_option_name}/--no-{default_option_name}"
            )
        else:
            default_option_declaration = f"--{default_option_name}"
        param_decls = [param.name]
        if parameter_info.param_decls:
            param_decls.extend(parameter_info.param_decls)
        else:
            param_decls.append(default_option_declaration)
        return (
            TyperOption(
                # Option
                param_decls=param_decls,
                show_default=parameter_info.show_default,
                prompt=parameter_info.prompt,
                confirmation_prompt=parameter_info.confirmation_prompt,
                prompt_required=parameter_info.prompt_required,
                hide_input=parameter_info.hide_input,
                is_flag=is_flag,
                flag_value=parameter_info.flag_value,
                multiple=is_list,
                count=parameter_info.count,
                allow_from_autoenv=parameter_info.allow_from_autoenv,
                type=parameter_type,
                help=parameter_info.help,
                hidden=parameter_info.hidden,
                show_choices=parameter_info.show_choices,
                show_envvar=parameter_info.show_envvar,
                # Parameter
                required=required,
                default=default_value,
                callback=get_param_callback(
                    callback=parameter_info.callback, convertor=convertor
                ),
                metavar=parameter_info.metavar,
                expose_value=parameter_info.expose_value,
                is_eager=parameter_info.is_eager,
                envvar=parameter_info.envvar,
                shell_complete=parameter_info.shell_complete,
                autocompletion=get_param_completion(parameter_info.autocompletion),
                # Rich settings
                rich_help_panel=parameter_info.rich_help_panel,
            ),
            convertor,
        )


def patch_typer_flag_value() -> None:
    typer.main.get_click_param = _patched_get_click_param
    typer.main.get_params_convertors_ctx_param_name_from_function = (
        get_params_convertors_ctx_param_name_from_function
    )


def unpatch_typer_flag_value() -> None:
    typer.main.get_click_param = _original_get_click_param
    typer.main.get_params_convertors_ctx_param_name_from_function = (
        _original_get_params_convertors_ctx_param_name_from_function
    )
