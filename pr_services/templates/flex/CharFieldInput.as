package {{ package_path }}.{{ model_name }}
{
    import net.poweru.generated.model.ValidatedTextInput;

    public class {{ class_name }}Input extends ValidatedTextInput
    {
        public static const MAXLENGTH:int = {{ field.max_length }};
        public static const REQUIRED:Boolean = {% if field.null %}false{% else %}true{% endif %};

        public function {{ class_name }}Input()
        {
            super();

            createTextValidation(REQUIRED, MAXLENGTH);
        }
    }
}
