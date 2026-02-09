from pydantic import BaseModel, Field, model_validator

class BridgeDataSchema(BaseModel):
    """
    Schema for validating Bridge Design parameters. 
    Includes physical constraints and engineering logic.
    """

    # --- Drawing Information ---
    drawing_number: str = Field(
        ..., 
        min_length=1, 
        description="Unique identifier for the engineering drawing. Required for file naming."
    )

    # --- Superstructure Dimensions (m and mm) ---
    length_m: float = Field(
        ..., 
        gt=0, 
        lt=200, 
        description="Total span length in meters. Must be positive and under 200m."
    )

    carriage_width_m: float = Field(
        ..., 
        gt=0, 
        lt=50, 
        description="Width of the carriageway in meters."
    )

    depth_mm: float = Field(
        ..., 
        gt=300, 
        lt=10000, 
        description="Girder depth in millimeters. Typically between 300mm and 10,000mm."
    )

    num_girders: int = Field(
        ..., 
        ge=2, 
        le=30, 
        description="Total number of longitudinal girders. Minimum of 2 required for stability."
    )

    # --- Pier Cap Dimensions (m) ---
    pier_cap_length_m: float = Field(
        ..., 
        gt=0, 
        description="Transverse length of the pier cap in meters."
    )

    pier_cap_depth_center_m: float = Field(
        ..., 
        gt=0, 
        description="Vertical depth of the pier cap at the center line."
    )

    pier_cap_depth_end_m: float = Field(
        ..., 
        gt=0, 
        description="Vertical depth of the pier cap at the cantilever ends."
    )

    pier_cap_width_m: float = Field(
        ..., 
        gt=0, 
        description="Horizontal width (thickness) of the pier cap."
    )

    # --- Engineering Logic Validations ---

    @model_validator(mode='after')
    def validate_structural_logic(self) -> 'BridgeDataSchema':
        """
        Global validation for engineering relationships.
        This runs after all individual fields are parsed.
        """
        
        # 1. Taper Logic: Center must be >= End
        if self.pier_cap_depth_center_m < self.pier_cap_depth_end_m:
            raise ValueError(
                f"Structural Taper Error: Center depth ({self.pier_cap_depth_center_m}m) "
                f"cannot be thinner than end depth ({self.pier_cap_depth_end_m}m)."
            )

        # 2. Transverse Fit: Width cannot exceed Pier Length
        if self.carriage_width_m > self.pier_cap_length_m:
            raise ValueError(
                f"Geometric Error: Carriage width ({self.carriage_width_m}m) "
                f"is wider than the Pier Cap support ({self.pier_cap_length_m}m)."
            )

        # 3. Girder Spacing: Must be at least 0.5m
        if self.num_girders > 1:
            spacing = self.carriage_width_m / (self.num_girders - 1)
            if spacing < 0.5:
                raise ValueError(f"Engineering Warning: Girder spacing ({spacing:.2f}m) is too narrow.")
        
        return self